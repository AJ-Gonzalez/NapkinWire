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

function resizeCanvas() {
    const container = document.querySelector('.canvas-container');
    const maxWidth = Math.min(window.innerWidth - 40, 1000);
    const aspectRatio = 600/1000; // height/width
    
    canvas.width = maxWidth;
    canvas.height = maxWidth * aspectRatio;
}

window.addEventListener('resize', resizeCanvas);

resizeCanvas(); // Initial size

function saveAsPNG() {
    // Create download link
    const link = document.createElement('a');
    link.download = 'diagram.png';
    link.href = canvas.toDataURL('image/png');
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Hook it up to your button
document.getElementById('save-png').addEventListener('click', saveAsPNG);