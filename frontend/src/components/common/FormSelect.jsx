export default function FormSelect({ label, options = [], ...props }) {
  return (
    <div className="form-group">
      <label>{label}</label>
      <select {...props}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}