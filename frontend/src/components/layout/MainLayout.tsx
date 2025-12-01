import { useTranscriptionStore } from '../../stores/transcriptionStore';
import { LeftPanel } from './LeftPanel';
import { RightPanel } from './RightPanel';
import { FileUploader } from '../upload/FileUploader';
import { UploadProgress } from '../upload/UploadProgress';

export function MainLayout() {
  const { status, transcription } = useTranscriptionStore();

  const showResults = status === 'completed' && transcription;
  const showProgress = status === 'pending' || status === 'processing';
  const showUploader = !status || status === 'failed';

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-surface-primary">
      {/* Header - Fixed height */}
      <header className="flex-shrink-0 bg-white border-b border-gray-100 z-50">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Nova</h1>
                <p className="text-xs text-gray-500">
                  Clinician Transcription Tool
                </p>
              </div>
            </div>

            {showResults && (
              <button
                onClick={() => useTranscriptionStore.getState().reset()}
                className="btn-secondary flex items-center gap-2 text-sm py-1.5 px-3"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                New Transcription
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content - Takes remaining height */}
      <main className="flex-1 overflow-hidden p-4">
        {showUploader && (
          <div className="h-full flex items-center justify-center">
            <div className="w-full max-w-2xl">
              <FileUploader />
            </div>
          </div>
        )}

        {showProgress && (
          <div className="h-full flex items-center justify-center">
            <UploadProgress />
          </div>
        )}

        {showResults && (
          <div className="h-full flex gap-4">
            {/* Left Panel - Clinical Data - Scrollable */}
            <aside className="w-72 flex-shrink-0 overflow-y-auto scrollbar-thin">
              <LeftPanel />
            </aside>

            {/* Right Panel - Timeline & Transcript - Takes remaining space */}
            <div className="flex-1 min-w-0 overflow-hidden">
              <RightPanel />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
