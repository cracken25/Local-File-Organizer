interface ConfidenceIndicatorProps {
  confidence: number;
}

export default function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps) {
  const getColor = () => {
    if (confidence >= 4) return 'text-green-500';
    if (confidence >= 3) return 'text-yellow-500';
    if (confidence >= 2) return 'text-orange-500';
    return 'text-red-500';
  };

  const stars = Array.from({ length: 5 }, (_, i) => i < confidence);

  return (
    <div className="flex items-center space-x-2">
      <div className={`flex ${getColor()}`}>
        {stars.map((filled, i) => (
          <span key={i}>{filled ? '★' : '☆'}</span>
        ))}
      </div>
      <span className="text-sm text-gray-600">({confidence}/5)</span>
    </div>
  );
}

