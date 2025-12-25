/**
 * Math Renderer Component
 * Renders LaTeX math expressions using KaTeX
 */

import { useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Renders inline or block math using KaTeX
 *
 * Usage:
 * <MathRenderer math="x^2 + y^2 = z^2" />
 * <MathRenderer math="\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}" block />
 */
export const MathRenderer = ({ math, block = false, className = '' }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current && math) {
      try {
        katex.render(math, containerRef.current, {
          throwOnError: false,
          displayMode: block,
          errorColor: '#EF4444',
        });
      } catch (error) {
        console.error('KaTeX error:', error);
        containerRef.current.textContent = math;
      }
    }
  }, [math, block]);

  return (
    <span
      ref={containerRef}
      className={`math-renderer ${block ? 'block' : 'inline'} ${className}`}
    />
  );
};

/**
 * Renders mixed text and math content
 * Supports inline math with $ delimiters and block math with $$ delimiters
 *
 * Usage:
 * <MathText text="The equation $x^2 + y^2 = z^2$ is famous" />
 */
export const MathText = ({ text, className = '' }) => {
  if (!text) return null;

  // Split by $$ (block math) and $ (inline math)
  const parts = [];
  let remaining = text;
  let key = 0;

  // First, extract block math ($$...$$)
  const blockRegex = /\$\$([\s\S]*?)\$\$/g;
  let lastIndex = 0;
  let match;

  while ((match = blockRegex.exec(text)) !== null) {
    // Add text before this match
    if (match.index > lastIndex) {
      const beforeText = text.slice(lastIndex, match.index);
      parts.push(...parseInlineMath(beforeText, key));
      key += 100;
    }

    // Add block math
    parts.push(
      <div key={`block-${key++}`} className="math-block my-3">
        <MathRenderer math={match[1].trim()} block />
      </div>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(...parseInlineMath(text.slice(lastIndex), key));
  }

  return <span className={className}>{parts}</span>;
};

// Helper to parse inline math ($...$)
function parseInlineMath(text, startKey) {
  const parts = [];
  const inlineRegex = /\$(.*?)\$/g;
  let lastIndex = 0;
  let match;
  let key = startKey;

  while ((match = inlineRegex.exec(text)) !== null) {
    // Add text before this match
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${key++}`}>
          {text.slice(lastIndex, match.index)}
        </span>
      );
    }

    // Add inline math
    parts.push(
      <MathRenderer key={`inline-${key++}`} math={match[1]} />
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${key++}`}>
        {text.slice(lastIndex)}
      </span>
    );
  }

  return parts;
}

/**
 * Math Input Component
 * Input field with live LaTeX preview
 */
export const MathInput = ({
  value,
  onChange,
  placeholder = 'Enter math expression (LaTeX supported)',
  label,
  error,
  helpText,
  rows = 3,
}) => {
  return (
    <div className="math-input-container">
      {label && <label className="form-label">{label}</label>}

      <textarea
        className={`form-textarea math-editor ${error ? 'error' : ''}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />

      {value && (
        <div className="math-preview mt-2">
          <small className="text-gray">Preview:</small>
          <div className="mt-1">
            <MathText text={value} />
          </div>
        </div>
      )}

      {error && <span className="form-error">{error}</span>}
      {helpText && !error && (
        <small className="text-gray mt-1 block">
          {helpText}
        </small>
      )}
    </div>
  );
};

/**
 * Common Math Symbols Toolbar
 */
export const MathToolbar = ({ onInsert }) => {
  const symbols = [
    { label: 'Fraction', latex: '\\frac{a}{b}', display: 'a/b' },
    { label: 'Square Root', latex: '\\sqrt{x}', display: '√x' },
    { label: 'Power', latex: 'x^{n}', display: 'xⁿ' },
    { label: 'Subscript', latex: 'x_{i}', display: 'xᵢ' },
    { label: 'Sum', latex: '\\sum_{i=1}^{n}', display: 'Σ' },
    { label: 'Integral', latex: '\\int_{a}^{b}', display: '∫' },
    { label: 'Infinity', latex: '\\infty', display: '∞' },
    { label: 'Pi', latex: '\\pi', display: 'π' },
    { label: 'Theta', latex: '\\theta', display: 'θ' },
    { label: 'Alpha', latex: '\\alpha', display: 'α' },
    { label: 'Beta', latex: '\\beta', display: 'β' },
    { label: 'Plus/Minus', latex: '\\pm', display: '±' },
    { label: 'Less/Equal', latex: '\\leq', display: '≤' },
    { label: 'Greater/Equal', latex: '\\geq', display: '≥' },
    { label: 'Not Equal', latex: '\\neq', display: '≠' },
    { label: 'Approximately', latex: '\\approx', display: '≈' },
  ];

  return (
    <div className="math-toolbar" style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.5rem',
      padding: '0.5rem',
      backgroundColor: 'var(--color-gray-100)',
      borderRadius: 'var(--radius-md)',
      marginBottom: '0.5rem',
    }}>
      {symbols.map((sym) => (
        <button
          key={sym.latex}
          type="button"
          onClick={() => onInsert(sym.latex)}
          title={sym.label}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '1rem',
            backgroundColor: 'white',
            border: '1px solid var(--color-gray-300)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => {
            e.target.style.backgroundColor = 'var(--color-primary-light)';
            e.target.style.color = 'white';
          }}
          onMouseOut={(e) => {
            e.target.style.backgroundColor = 'white';
            e.target.style.color = 'inherit';
          }}
        >
          {sym.display}
        </button>
      ))}
    </div>
  );
};

export default MathRenderer;
