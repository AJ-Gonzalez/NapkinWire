const canvas = document.getElementById('diagramCanvas');
const ctx = canvas.getContext('2d');

// Example shapes drawn on canvas
ctx.strokeStyle = '#ff0000';
ctx.lineWidth = 2;

// Rectangle (Start Process)
ctx.strokeRect(100, 50, 150, 80);

// Diamond (Decision) - simplified as rotated square
ctx.strokeRect(350, 150, 150, 80);

// Rectangle (Action)
ctx.strokeRect(600, 250, 150, 80);

console.log('Canvas ready for diagram mockup');
