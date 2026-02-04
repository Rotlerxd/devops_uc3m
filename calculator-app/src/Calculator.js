import React, { useState } from 'react';
import './Calculator.css';

function Calculator() {
  const [display, setDisplay] = useState('0');
  const [previousValue, setPreviousValue] = useState(null);
  const [operation, setOperation] = useState(null);
  const [waitingForOperand, setWaitingForOperand] = useState(false);

  const inputDigit = (digit) => {
    if (waitingForOperand) {
      setDisplay(String(digit));
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? String(digit) : display + digit);
    }
  };

  const inputDecimal = () => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
    } else if (display.indexOf('.') === -1) {
      setDisplay(display + '.');
    }
  };

  const clear = () => {
    setDisplay('0');
    setPreviousValue(null);
    setOperation(null);
    setWaitingForOperand(false);
  };

  const performOperation = (nextOperation) => {
    const inputValue = parseFloat(display);

    if (previousValue === null) {
      setPreviousValue(inputValue);
    } else if (operation) {
      const currentValue = previousValue || 0;
      const newValue = calculate(currentValue, inputValue, operation);

      setDisplay(String(newValue));
      setPreviousValue(newValue);
    }

    setWaitingForOperand(true);
    setOperation(nextOperation);
  };

  const calculate = (leftOperand, rightOperand, operation) => {
    switch (operation) {
      case '+':
        return leftOperand + rightOperand;
      case '-':
        return leftOperand - rightOperand;
      case '*':
        return leftOperand * rightOperand;
      case '/':
        return leftOperand / rightOperand;
      case '=':
        return rightOperand;
      default:
        return rightOperand;
    }
  };

  const equals = () => {
    const inputValue = parseFloat(display);

    if (previousValue !== null && operation) {
      const newValue = calculate(previousValue, inputValue, operation);
      setDisplay(String(newValue));
      setPreviousValue(null);
      setOperation(null);
      setWaitingForOperand(true);
    }
  };

  return (
    <div className="calculator">
      <div className="calculator-display">{display}</div>
      <div className="calculator-keypad">
        <div className="calculator-row">
          <button className="calculator-key key-clear" onClick={clear}>C</button>
          <button className="calculator-key key-sign" onClick={() => setDisplay(String(-parseFloat(display)))}>±</button>
          <button className="calculator-key key-percent" onClick={() => setDisplay(String(parseFloat(display) / 100))}>%</button>
          <button className="calculator-key key-operator" onClick={() => performOperation('/')}>÷</button>
        </div>
        <div className="calculator-row">
          <button className="calculator-key" onClick={() => inputDigit(7)}>7</button>
          <button className="calculator-key" onClick={() => inputDigit(8)}>8</button>
          <button className="calculator-key" onClick={() => inputDigit(9)}>9</button>
          <button className="calculator-key key-operator" onClick={() => performOperation('*')}>×</button>
        </div>
        <div className="calculator-row">
          <button className="calculator-key" onClick={() => inputDigit(4)}>4</button>
          <button className="calculator-key" onClick={() => inputDigit(5)}>5</button>
          <button className="calculator-key" onClick={() => inputDigit(6)}>6</button>
          <button className="calculator-key key-operator" onClick={() => performOperation('-')}>−</button>
        </div>
        <div className="calculator-row">
          <button className="calculator-key" onClick={() => inputDigit(1)}>1</button>
          <button className="calculator-key" onClick={() => inputDigit(2)}>2</button>
          <button className="calculator-key" onClick={() => inputDigit(3)}>3</button>
          <button className="calculator-key key-operator" onClick={() => performOperation('+')}>+</button>
        </div>
        <div className="calculator-row">
          <button className="calculator-key key-zero" onClick={() => inputDigit(0)}>0</button>
          <button className="calculator-key" onClick={inputDecimal}>.</button>
          <button className="calculator-key key-equals" onClick={equals}>=</button>
        </div>
      </div>
    </div>
  );
}

export default Calculator;
