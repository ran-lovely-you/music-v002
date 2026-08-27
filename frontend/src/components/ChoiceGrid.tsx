interface ChoiceOption {
  key: string;
  label: string;
  description?: string;
}

interface ChoiceGridProps {
  options: ChoiceOption[];
  selected: string[];
  multi?: boolean;
  onChange: (next: string[]) => void;
}

export function ChoiceGrid({ options, selected, multi = true, onChange }: ChoiceGridProps) {
  const toggle = (key: string) => {
    if (multi) {
      if (selected.includes(key)) {
        onChange(selected.filter((k) => k !== key));
      } else {
        onChange([...selected, key]);
      }
    } else {
      onChange([key]);
    }
  };

  return (
    <div className="choice-grid">
      {options.map((opt) => {
        const isSelected = selected.includes(opt.key);
        return (
          <button
            key={opt.key}
            type="button"
            className={`choice-card${isSelected ? " selected" : ""}`}
            aria-pressed={isSelected}
            onClick={() => toggle(opt.key)}
          >
            <span>{opt.label}</span>
            {opt.description && <span className="choice-description">{opt.description}</span>}
          </button>
        );
      })}
    </div>
  );
}
