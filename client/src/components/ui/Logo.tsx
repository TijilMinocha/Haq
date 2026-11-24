interface LogoProps {
  className?: string;
}

export function Logo({ className = 'h-8 w-8 sm:h-9 sm:w-9' }: LogoProps) {
  return (
    <img
      src="/logo.jpg"
      alt="Haq logo"
      className={`shrink-0 rounded-lg object-cover shadow-2xs ${className}`}
    />
  );
}
