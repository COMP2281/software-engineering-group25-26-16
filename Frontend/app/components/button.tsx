export function Button({
  children,
  onClick,
  className = "",
  style = {},
}: {
  children: string;
  onClick: () => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const base_classes =
    "rounded-sm p-5 px-4 py-2 transition-colors duration-200 m-1";
  return (
    <button
      onClick={onClick}
      className={
        base_classes +
        " " +
        (className == ""
          ? "bg-primary hover:bg-primary/90 cursor-pointer text-white"
          : className)
      }
      style={style}
    >
      {children}
    </button>
  );
}
