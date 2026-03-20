export const formatNumber = (value) => {
  const numeric = Number(value ?? 0);
  return numeric.toLocaleString(undefined, { maximumFractionDigits: 2 });
};

export const formatPercent = (value) => `${formatNumber(value)}%`;

export const formatDate = (value) => {
  if (!value) return "-";
  return new Date(value).toLocaleDateString();
};