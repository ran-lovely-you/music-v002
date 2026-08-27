import { ja } from "../i18n/ja";

interface StepNavProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
}

export function StepNav({ onBack, onNext, nextLabel, nextDisabled }: StepNavProps) {
  return (
    <div className="nav-row">
      {onBack ? (
        <button type="button" className="big-button secondary" onClick={onBack}>
          {ja.nav.back}
        </button>
      ) : (
        <span />
      )}
      {onNext && (
        <button type="button" className="big-button" onClick={onNext} disabled={nextDisabled}>
          {nextLabel ?? ja.nav.next}
        </button>
      )}
    </div>
  );
}
