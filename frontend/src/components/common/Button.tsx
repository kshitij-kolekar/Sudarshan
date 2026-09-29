import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'subtle';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium tracking-tight transition-colors duration-150 rounded border focus:outline-none focus:ring-2 focus:ring-terracotta/40 focus:ring-offset-1 select-none';

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-3.5 py-2 gap-2',
    lg: 'text-sm px-5 py-2.5 gap-2.5',
  };

  const variantStyles = {
    primary: disabled
      ? 'bg-charcoal-300/40 text-charcoal-400 border-border cursor-not-allowed'
      : 'bg-terracotta text-white border-terracotta hover:bg-terracotta-hover active:bg-charcoal-900 shadow-sm',
    secondary: disabled
      ? 'bg-surface-subtle text-charcoal-400 border-border cursor-not-allowed'
      : 'bg-surface text-charcoal-700 border-border hover:bg-surface-subtle hover:text-charcoal-900 hover:border-charcoal-300 shadow-subtle',
    outline: disabled
      ? 'bg-transparent text-charcoal-300 border-border cursor-not-allowed'
      : 'bg-transparent text-charcoal-700 border-border hover:border-charcoal-400 hover:text-charcoal-900',
    subtle: disabled
      ? 'bg-transparent text-charcoal-300 border-transparent cursor-not-allowed'
      : 'bg-transparent text-charcoal-600 border-transparent hover:bg-surface-subtle hover:text-charcoal-900',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
      {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
    </button>
  );
};
