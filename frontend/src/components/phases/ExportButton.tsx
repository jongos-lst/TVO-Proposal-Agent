import { getExportUrl } from '../../api/client';

interface Props {
  sessionId: string;
  ready: boolean;
}

export default function ExportButton({ sessionId, ready }: Props) {
  if (!ready) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Export
      </h4>
      <a
        href={getExportUrl(sessionId)}
        download
        className="block w-full text-center bg-green-600 hover:bg-green-700 text-white rounded-lg px-4 py-3 text-sm font-medium transition-colors"
      >
        Download PowerPoint
      </a>
    </div>
  );
}
