import { useTranscriptionStore } from '../../stores/transcriptionStore';
import { ActionItemsList } from '../clinical/ActionItemsList';
import { NumericalValues } from '../clinical/NumericalValues';
import { OrchestratorDecisions } from '../clinical/OrchestratorDecisions';

export function LeftPanel() {
  const { clinicalData, orchestratorDecisions, transcription } =
    useTranscriptionStore();

  if (!clinicalData) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* Summary Card */}
      <div className="card p-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Summary
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-marker-action/30 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-amber-700">
              {clinicalData.action_items.length}
            </div>
            <div className="text-[10px] text-amber-600">Action Items</div>
          </div>
          <div className="bg-marker-numerical/30 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-green-700">
              {clinicalData.numerical_values.length}
            </div>
            <div className="text-[10px] text-green-600">Values</div>
          </div>
          <div className="bg-marker-resolved/30 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-purple-700">
              {orchestratorDecisions.length}
            </div>
            <div className="text-[10px] text-purple-600">Resolved</div>
          </div>
          <div className="bg-gray-100 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-gray-700">
              {transcription
                ? Math.round((transcription.overall_confidence || 0) * 100)
                : 0}
              %
            </div>
            <div className="text-[10px] text-gray-500">Confidence</div>
          </div>
        </div>
      </div>

      {/* Action Items */}
      <ActionItemsList items={clinicalData.action_items} />

      {/* Numerical Values */}
      <NumericalValues values={clinicalData.numerical_values} />

      {/* Orchestrator Decisions */}
      {orchestratorDecisions.length > 0 && (
        <OrchestratorDecisions decisions={orchestratorDecisions} />
      )}

      {/* Medical Terms */}
      {clinicalData.medical_terms.length > 0 && (
        <div className="card p-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Medical Terms
          </h3>
          <div className="flex flex-wrap gap-1">
            {clinicalData.medical_terms.map((term, index) => (
              <span
                key={index}
                className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] rounded-full"
              >
                {term}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
