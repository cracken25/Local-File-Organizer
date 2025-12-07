import { Check } from 'lucide-react';

interface StepIndicatorProps {
    step: number;
    title: string;
    description: string;
    isActive: boolean;
    isCompleted: boolean;
    onClick: () => void;
}

export default function StepIndicator({
    step,
    title,
    description,
    isActive,
    isCompleted,
    onClick,
}: StepIndicatorProps) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center p-3 rounded-lg transition-colors text-left ${isActive
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
        >
            <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-3 ${isCompleted
                        ? 'bg-green-100 text-green-600'
                        : isActive
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-500'
                    }`}
            >
                {isCompleted ? <Check size={16} /> : step}
            </div>
            <div>
                <div
                    className={`text-sm font-medium ${isActive ? 'text-blue-900' : 'text-gray-900'
                        }`}
                >
                    {title}
                </div>
                <div className="text-xs text-gray-500">{description}</div>
            </div>
        </button>
    );
}
