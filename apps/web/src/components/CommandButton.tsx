import type { ButtonHTMLAttributes, ReactNode } from 'react';

export interface CommandButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'rust' | 'pine' | 'ochre' | 'ghost';
  busy?: boolean;
  children: ReactNode;
}

/** A stamped press-tool button. `busy` keeps the label but disables the press
 *  and announces the pending state to assistive tech. */
export function CommandButton({
  variant = 'rust',
  busy = false,
  disabled,
  children,
  className,
  ...rest
}: CommandButtonProps) {
  const variantClass = variant === 'rust' ? '' : ` command-btn--${variant}`;
  return (
    <button
      type="button"
      className={`command-btn${variantClass}${className ? ` ${className}` : ''}`}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      {...rest}
    >
      {children}
    </button>
  );
}
