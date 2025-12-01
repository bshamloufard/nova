import { useCallback, useState } from 'react';
import { useTranscriptionStore } from '../../stores/transcriptionStore';
import { usePlayerStore } from '../../stores/playerStore';
import { uploadAudio, pollForCompletion, getAudioUrl } from '../../services/api';

export function FileUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const { setJobId, setStatus, setProgress, setError, setResult, error } =
    useTranscriptionStore();
  const { setAudioUrl, setDurationMs } = usePlayerStore();

  const handleFile = useCallback(async (selectedFile: File) => {
    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/ogg', 'audio/x-m4a'];
    const validExtensions = ['.mp3', '.wav', '.m4a', '.ogg'];
    
    const hasValidType = validTypes.includes(selectedFile.type);
    const hasValidExtension = validExtensions.some(ext => 
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!hasValidType && !hasValidExtension) {
      setError('Invalid file type. Please upload an MP3, WAV, M4A, or OGG file.');
      return;
    }

    // Validate file size (100MB max)
    const maxSize = 100 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      setError('File too large. Maximum size is 100MB.');
      return;
    }

    setFile(selectedFile);
    setError(null);

    try {
      // Upload the file
      setStatus('pending');
      setProgress(0);

      const job = await uploadAudio(selectedFile);
      setJobId(job.job_id);
      setStatus('processing');

      // Set audio URL for playback
      setAudioUrl(getAudioUrl(job.job_id));

      // Poll for completion
      const result = await pollForCompletion(job.job_id, (progress) => {
        setProgress(progress);
      });

      // Set the result
      if (result.result) {
        setResult(result.result);
        setDurationMs(result.result.timeline.duration_ms);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStatus('failed');
    }
  }, [setJobId, setStatus, setProgress, setError, setResult, setAudioUrl, setDurationMs]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFile(droppedFile);
      }
    },
    [handleFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFile(selectedFile);
      }
    },
    [handleFile]
  );

  return (
    <div className="card p-8">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload Audio Recording
        </h2>
        <p className="text-gray-500">
          Upload a clinical audio recording for intelligent transcription with
          multi-model orchestration.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center
          transition-all duration-200 cursor-pointer
          ${
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
          }
        `}
      >
        <input
          type="file"
          accept=".mp3,.wav,.m4a,.ogg,audio/*"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <div className="flex flex-col items-center">
          <div
            className={`
              w-16 h-16 rounded-full flex items-center justify-center mb-4
              ${isDragging ? 'bg-primary-100' : 'bg-gray-100'}
            `}
          >
            <svg
              className={`w-8 h-8 ${isDragging ? 'text-primary-600' : 'text-gray-400'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <p className="text-gray-700 font-medium mb-1">
            {isDragging
              ? 'Drop your file here'
              : 'Drag and drop your audio file here'}
          </p>
          <p className="text-gray-500 text-sm mb-4">
            or click to browse
          </p>

          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className="px-2 py-1 bg-gray-100 rounded">MP3</span>
            <span className="px-2 py-1 bg-gray-100 rounded">WAV</span>
            <span className="px-2 py-1 bg-gray-100 rounded">M4A</span>
            <span className="px-2 py-1 bg-gray-100 rounded">OGG</span>
            <span className="text-gray-300">•</span>
            <span>Max 100MB</span>
          </div>
        </div>
      </div>

      {/* Error message */}
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

      {/* Selected file info */}
      {file && !error && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-5 h-5 text-primary-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Features list */}
      <div className="mt-8 grid grid-cols-2 gap-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-marker-resolved/30 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 text-sm">Multi-Model Orchestration</h4>
            <p className="text-xs text-gray-500">3 AI models for uncertain segments</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-marker-action/30 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 text-sm">Action Item Detection</h4>
            <p className="text-xs text-gray-500">Auto-extract clinical tasks</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-marker-numerical/30 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 text-sm">Numerical Extraction</h4>
            <p className="text-xs text-gray-500">Vitals, labs, and dosages</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 text-sm">Interactive Timeline</h4>
            <p className="text-xs text-gray-500">Karaoke-style playback</p>
          </div>
        </div>
      </div>
    </div>
  );
}

