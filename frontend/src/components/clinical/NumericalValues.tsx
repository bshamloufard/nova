import { usePlayerStore } from '../../stores/playerStore';
import type { NumericalValue, NumericalCategory } from '../../types';

interface NumericalValuesProps {
  values: NumericalValue[];
}

const CATEGORY_ICONS: Record<NumericalCategory, string> = {
  vital: '❤️',
  lab: '🔬',
  measurement: '📏',
  dosage: '💊',
};

const CATEGORY_LABELS: Record<NumericalCategory, string> = {
  vital: 'Vitals',
  lab: 'Lab Values',
  measurement: 'Measurements',
  dosage: 'Dosages',
};

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function NumericalValues({ values }: NumericalValuesProps) {
  const { setCurrentTimeMs } = usePlayerStore();

  if (values.length === 0) {
    return (
      <div className="card p-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span>🔢</span>
          Numerical Values
        </h3>
        <p className="text-xs text-gray-400 text-center py-2">
          No numerical values detected
        </p>
      </div>
    );
  }

  // Group values by category
  const groupedValues = values.reduce<Record<string, NumericalValue[]>>(
    (acc, value) => {
      const category = value.category;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(value);
      return acc;
    },
    {}
  );

  return (
    <div className="card p-3">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <span>🔢</span>
        Numerical Values
        <span className="ml-auto bg-marker-numerical/50 text-green-700 px-1.5 py-0.5 rounded-full text-[10px]">
          {values.length}
        </span>
      </h3>

      <div className="space-y-3 max-h-40 overflow-y-auto scrollbar-thin pr-1">
        {Object.entries(groupedValues).map(([category, categoryValues]) => (
          <div key={category}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs">
                {CATEGORY_ICONS[category as NumericalCategory] || '📊'}
              </span>
              <span className="text-[10px] font-medium text-gray-400 uppercase">
                {CATEGORY_LABELS[category as NumericalCategory] || category}
              </span>
            </div>

            <div className="grid gap-1">
              {categoryValues.map((value, index) => (
                <div
                  key={index}
                  onClick={() => setCurrentTimeMs(value.timestamp_ms)}
                  className="flex items-center justify-between p-1.5 bg-marker-numerical/20 
                             rounded-lg hover:bg-marker-numerical/40 cursor-pointer 
                             transition-colors group"
                >
                  <span className="text-xs text-gray-600">{value.label}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono font-semibold text-xs text-green-700">
                      {value.value}
                      {value.unit && (
                        <span className="text-green-600 text-[10px] ml-0.5">
                          {value.unit}
                        </span>
                      )}
                    </span>
                    <span className="text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      {formatTime(value.timestamp_ms)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
