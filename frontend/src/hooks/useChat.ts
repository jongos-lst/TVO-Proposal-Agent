import { useState, useCallback, useRef } from 'react';
import type { Message, ProposalState, SSEEvent, Phase, CustomerPersona, CalculationParams } from '../types';
import { sendMessageStream, submitIntake, overridePhase, submitConfirmedCalculation } from '../api/client';

const generateId = () => Math.random().toString(36).substring(2, 15);

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [proposal, setProposal] = useState<ProposalState>({
    phase: 'intake',
    proposalApproved: false,
  });
  const [showConfirmation, setShowConfirmation] = useState(false);
  const streamingContentRef = useRef('');

  const handleStateUpdate = useCallback((update: SSEEvent) => {
    setProposal(prev => ({
      ...prev,
      phase: prev.phase,  // Phase changes only via explicit button clicks
      persona: update.persona || prev.persona,
      selectedProducts: update.selected_products || prev.selectedProducts,
      tvoResults: update.tvo_results || prev.tvoResults,
      competitiveAdvantages: update.competitive_advantages || prev.competitiveAdvantages,
      competitorProductNames: update.competitor_product_names || prev.competitorProductNames,
      proposalApproved: update.proposal_approved !== undefined ? update.proposal_approved : prev.proposalApproved,
      pptxPath: update.pptx_path || prev.pptxPath,
    }));
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming || !content.trim()) return;

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);

    const assistantId = generateId();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMsg]);
    setIsStreaming(true);
    streamingContentRef.current = '';

    try {
      await sendMessageStream(
        sessionId,
        content.trim(),
        (token) => {
          streamingContentRef.current += token;
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: streamingContentRef.current }
                : m
            )
          );
        },
        handleStateUpdate,
        () => {
          setIsStreaming(false);
        },
        (error) => {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: `Error: ${error}` }
                : m
            )
          );
          setIsStreaming(false);
        }
      );
    } catch (err) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, content: `Connection error: ${err}` }
            : m
        )
      );
      setIsStreaming(false);
    }
  }, [sessionId, isStreaming, handleStateUpdate]);

  const submitPersona = useCallback(async (persona: CustomerPersona) => {
    setIsStreaming(true);
    try {
      const result = await submitIntake(sessionId, persona as Record<string, unknown>);
      if (result.success) {
        const parts: string[] = [];
        if (persona.customer_name) parts.push(`**Customer:** ${persona.customer_name}`);
        if (persona.industry) parts.push(`**Industry:** ${persona.industry}`);
        if (persona.pain_points?.length) parts.push(`**Pain Points:** ${persona.pain_points.join(', ')}`);
        if (persona.use_scenarios?.length) parts.push(`**Use Scenarios:** ${persona.use_scenarios.join(', ')}`);
        if (persona.budget_amount) parts.push(`**Budget:** $${persona.budget_amount.toLocaleString()}`);
        if (persona.service_warranty_needs) parts.push(`**Warranty:** ${persona.service_warranty_needs}`);
        if (persona.current_devices?.length) parts.push(`**Current Devices:** ${persona.current_devices.join(', ')}`);
        if (persona.fleet_size) parts.push(`**Fleet Size:** ${persona.fleet_size}`);

        setMessages([
          {
            id: generateId(),
            role: 'user',
            content: `Customer intake form submitted:\n${parts.join('\n')}`,
            timestamp: new Date(),
          },
          {
            id: generateId(),
            role: 'assistant',
            content: `Thank you! I've recorded the customer profile for ${persona.customer_name || 'your customer'}. All required information has been collected.\n\nLet's move on to **product recommendation**. Which Getac product(s) would you like to recommend for this customer? You can select one or multiple products.`,
            timestamp: new Date(),
          },
        ]);

        setProposal(prev => ({
          ...prev,
          phase: 'recommendation',
          persona,
        }));
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: generateId(),
        role: 'assistant',
        content: `Error submitting intake: ${err}`,
        timestamp: new Date(),
      }]);
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId]);

  const goToPhase = useCallback(async (targetPhase: Phase) => {
    setIsStreaming(true);
    try {
      const result = await overridePhase(sessionId, targetPhase);
      if (result.status === 'success') {
        setProposal(prev => ({
          ...prev,
          phase: targetPhase,
          persona: result.persona || prev.persona,
          selectedProducts: result.selected_products || prev.selectedProducts,
          tvoResults: result.tvo_results || prev.tvoResults,
          competitiveAdvantages: result.competitive_advantages || prev.competitiveAdvantages,
          competitorProductNames: result.competitor_product_names || prev.competitorProductNames,
          proposalApproved: result.proposal_approved ?? prev.proposalApproved,
        }));
        setMessages(prev => [...prev, {
          id: generateId(),
          role: 'assistant',
          content: `Navigated back to **${targetPhase}** phase. You can review and edit the information, then continue forward when ready.`,
          timestamp: new Date(),
        }]);
      }
    } catch (err) {
      console.error("Error changing phase:", err);
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId]);

  const confirmCalculation = useCallback(async (params: CalculationParams) => {
    setIsStreaming(true);
    setShowConfirmation(false);
    try {
      const result = await submitConfirmedCalculation(sessionId, params);
      if (result.success) {
        setProposal(prev => ({
          ...prev,
          phase: result.phase || 'calculation',
          tvoResults: result.tvo_results || prev.tvoResults,
          selectedProducts: result.selected_products || prev.selectedProducts,
        }));

        // Add a summary message
        const productCount = params.products.length;
        setMessages(prev => [...prev, {
          id: generateId(),
          role: 'user',
          content: `Confirmed TVO calculation parameters: ${params.fleet_size} units, ${params.deployment_years}-year deployment, $${params.hourly_productivity_value}/hr productivity value for ${productCount} product(s).`,
          timestamp: new Date(),
        }]);

        // Trigger the LLM to present the TVO numbers
        await sendMessageStream(
          sessionId,
          `Present the TVO calculation results. Parameters: ${params.fleet_size} units fleet, ${params.deployment_years}-year deployment.`,
          (token) => {
            streamingContentRef.current += token;
            setMessages(prev => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === 'assistant') {
                return prev.map((m, i) => i === prev.length - 1 ? { ...m, content: streamingContentRef.current } : m);
              }
              return [...prev, { id: generateId(), role: 'assistant', content: streamingContentRef.current, timestamp: new Date() }];
            });
          },
          handleStateUpdate,
          () => { setIsStreaming(false); },
          (error) => {
            setMessages(prev => [...prev, {
              id: generateId(),
              role: 'assistant',
              content: `TVO calculation complete. Use the data panel on the left to review the results.\n\n(Note: ${error})`,
              timestamp: new Date(),
            }]);
            setIsStreaming(false);
          }
        );
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: generateId(),
        role: 'assistant',
        content: `Error calculating TVO: ${err}`,
        timestamp: new Date(),
      }]);
      setIsStreaming(false);
    }
  }, [sessionId, handleStateUpdate]);

  const approveAndGenerate = useCallback(async () => {
    setIsStreaming(true);
    try {
      // Set proposal_approved and advance phase to generation
      const result = await overridePhase(sessionId, 'generation', true);
      if (result.status === 'success') {
        setProposal(prev => ({
          ...prev,
          phase: 'generation',
          proposalApproved: true,
          persona: result.persona || prev.persona,
          selectedProducts: result.selected_products || prev.selectedProducts,
          tvoResults: result.tvo_results || prev.tvoResults,
          competitiveAdvantages: result.competitive_advantages || prev.competitiveAdvantages,
          competitorProductNames: result.competitor_product_names || prev.competitorProductNames,
        }));
      }

      // Trigger the generation node by sending a message
      const assistantId = generateId();
      setMessages(prev => [...prev, {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }]);
      streamingContentRef.current = '';

      await sendMessageStream(
        sessionId,
        'Generate the TVO proposal deck.',
        (token) => {
          streamingContentRef.current += token;
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: streamingContentRef.current }
                : m
            )
          );
        },
        (update) => {
          handleStateUpdate(update);
          // Check if generation completed (pptx_path present or phase is complete)
          if (update.pptx_path || update.phase === 'complete') {
            setProposal(prev => ({
              ...prev,
              phase: 'complete',
              pptxPath: update.pptx_path || prev.pptxPath,
            }));
          }
        },
        () => { setIsStreaming(false); },
        (error) => {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: `Error generating deck: ${error}` }
                : m
            )
          );
          setIsStreaming(false);
        }
      );
    } catch (err) {
      console.error('Error in approveAndGenerate:', err);
      setIsStreaming(false);
    }
  }, [sessionId, handleStateUpdate]);

  return { messages, isStreaming, proposal, sendMessage, submitPersona, goToPhase, showConfirmation, setShowConfirmation, confirmCalculation, approveAndGenerate };
}
