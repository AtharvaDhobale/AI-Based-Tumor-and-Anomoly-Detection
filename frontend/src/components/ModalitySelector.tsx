import clsx from "clsx";
import type { Modality, ModalityInfo } from "../lib/api";
import { MODALITY_INFO } from "../lib/api";

interface Props {
  selected: Modality;
  onChange: (m: Modality) => void;
}

export default function ModalitySelector({ selected, onChange }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {(Object.entries(MODALITY_INFO) as [Modality, ModalityInfo][]).map(
        ([key, info]) => (
          <button
            key={key}
            onClick={() => onChange(key)}
            className={clsx(
              "card p-4 text-left transition-all duration-200 hover:border-medical-600",
              selected === key
                ? "border-medical-500 bg-medical-950/30 ring-1 ring-medical-500"
                : "hover:bg-gray-800/50"
            )}
          >
            <div className="text-2xl mb-2">{info.icon}</div>
            <div className="font-semibold text-sm text-white">{info.label}</div>
            <div className="text-xs text-gray-500 mt-1 leading-relaxed">{info.description}</div>
          </button>
        )
      )}
    </div>
  );
}