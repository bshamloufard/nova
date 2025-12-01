import { useTranscriptionStore } from '../../stores/transcriptionStore';

export function UploadProgress() {
  const { status, progress, error } = useTranscriptionStore();

  const progressPercent = Math.round(progress * 100);

  const stages = [
    { key: 'upload', label: 'Uploading', threshold: 0.1 },
    { key: 'primary', label: 'Primary Transcription', threshold: 0.3 },
    { key: 'analyzing', label: 'Analyzing Confidence', threshold: 0.5 },
    { key: 'orchestrating', label: 'Multi-Model Orchestration', threshold: 0.7 },
    { key: 'extracting', label: 'Clinical Extraction', threshold: 0.85 },
    { key: 'finalizing', label: 'Finalizing', threshold: 1.0 },
  ];

  const currentStage = stages.findIndex((s) => progress < s.threshold);
  const activeStage = currentStage === -1 ? stages.length - 1 : currentStage;

  return (
    <div className="max-w-xl mx-auto">
      <div className="card p-8">
        <div className="text-center mb-8">
          <div className="relative w-24 h-24 mx-auto mb-4">
            {/* Spinning ring */}
            <svg
              className="w-24 h-24 animate-spin"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#E0E7FF"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#6366F1"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${progressPercent * 2.51} 251`}
                transform="rotate(-90 50 50)"
              />
            </svg>
            {/* Percentage text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold text-gray-900">
                {progressPercent}%
              </span>
            </div>
          </div>

          <h2 className="text-xl font-bold text-gray-900 mb-1">
            Processing Your Recording
          </h2>
          <p className="text-gray-500">
            {stages[activeStage]?.label || 'Processing...'}
          </p>
        </div>

        {/* Progress stages */}
        <div className="space-y-3">
          {stages.map((stage, index) => {
            const isComplete = progress >= stage.threshold;
            const isActive = index === activeStage;

            return (
              <div
                key={stage.key}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-all duration-300
                  ${isComplete ? 'bg-green-50' : isActive ? 'bg-primary-50' : 'bg-gray-50'}
                `}
              >
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${
                      isComplete
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-primary-500 text-white animate-pulse'
                        : 'bg-gray-200 text-gray-400'
                    }
                  `}
                >
                  {isComplete ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                <span
                  className={`
                    font-medium
                    ${isComplete ? 'text-green-700' : isActive ? 'text-primary-700' : 'text-gray-400'}
                  `}
                >
                  {stage.label}
                </span>
                {isActive && (
                  <div className="ml-auto">
                    <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Tips */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="text-sm text-blue-700 font-medium">
                Multi-Model Orchestration Active
              </p>
              <p className="text-xs text-blue-600 mt-1">
                When confidence is low, Nova consults multiple AI models and uses
                an LLM to select the best transcription.
              </p>
            </div>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="font-medium">{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

