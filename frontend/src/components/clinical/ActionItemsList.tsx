import { usePlayerStore } from '../../stores/playerStore';
import type { ActionItem } from '../../types';
import { CATEGORY_INFO, PRIORITY_INFO } from '../../types';

interface ActionItemsListProps {
  items: ActionItem[];
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function ActionItemsList({ items }: ActionItemsListProps) {
  const { setCurrentTimeMs } = usePlayerStore();

  if (items.length === 0) {
    return (
      <div className="card p-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span>📋</span>
          Action Items
        </h3>
        <p className="text-xs text-gray-400 text-center py-2">
          No action items detected
        </p>
      </div>
    );
  }

  // Group items by category
  const groupedItems = items.reduce<Record<string, ActionItem[]>>((acc, item) => {
    const category = item.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {});

  return (
    <div className="card p-3">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <span>📋</span>
        Action Items
        <span className="ml-auto bg-marker-action/50 text-amber-700 px-1.5 py-0.5 rounded-full text-[10px]">
          {items.length}
        </span>
      </h3>

      <div className="space-y-3 max-h-40 overflow-y-auto scrollbar-thin pr-1">
        {Object.entries(groupedItems).map(([category, categoryItems]) => {
          const categoryInfo = CATEGORY_INFO[category as keyof typeof CATEGORY_INFO];
          
          return (
            <div key={category}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-xs">{categoryInfo?.icon || '📌'}</span>
                <span className="text-[10px] font-medium text-gray-400 uppercase">
                  {categoryInfo?.label || category}
                </span>
              </div>

              <div className="space-y-1">
                {categoryItems.map((item, index) => {
                  const priorityInfo = PRIORITY_INFO[item.priority];

                  return (
                    <div
                      key={index}
                      onClick={() => setCurrentTimeMs(item.timestamp_ms)}
                      className="p-2 bg-gray-50 rounded-lg hover:bg-marker-action/20 
                                 cursor-pointer transition-colors group"
                    >
                      <div className="flex items-start justify-between gap-1">
                        <p className="text-xs text-gray-700 flex-1 line-clamp-2">
                          {item.text}
                        </p>
                        <span
                          className={`
                            px-1 py-0.5 text-[10px] rounded flex-shrink-0
                            ${priorityInfo?.color || 'bg-gray-100 text-gray-600'}
                          `}
                        >
                          {priorityInfo?.label || item.priority}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center text-[10px] text-gray-400">
                        <span>{formatTime(item.timestamp_ms)}</span>
                        <span className="opacity-0 group-hover:opacity-100 transition-opacity ml-auto text-primary-500">
                          Jump →
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
