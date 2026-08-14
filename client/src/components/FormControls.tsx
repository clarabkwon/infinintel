import type { ChangeEvent, ReactNode } from "react";

interface FieldProps {
  label: string;
  children: ReactNode;
}

export function Field({ label, children }: FieldProps) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
    </div>
  );
}

type NumberChange = (value: number) => void;

export function numberHandler(onChange: NumberChange) {
  return (e: ChangeEvent<HTMLInputElement>) => {
    onChange(Number(e.target.value));
  };
}

export function stringHandler(onChange: (value: string) => void) {
  return (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    onChange(e.target.value);
  };
}
