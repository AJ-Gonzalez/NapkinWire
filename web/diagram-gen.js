import { getMousePos, getTouchPos, snapToGrid } from './shared/ascii-converter.js';

const canvas = document.getElementById('diagramCanvas');
const ctx = canvas.getContext('2d');

// Touch detection for snap grid
const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
const snapSize = isTouchDevice ? 15 : 10;

let currentShape = 'rectangle';
let isDrawing = false;
let startX, startY;
let shapes = []; // Store all drawn shapes

// Shape toolbar handling
document.querySelectorAll('.shape-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Clear all active states
        document.querySelectorAll('.shape-btn').forEach(b => b.classList.remove('active'));
        // Set this button as active
        this.classList.add('active');
        // Update current shape
        currentShape = this.dataset.shape;
    });
});

// Mouse events
canvas.addEventListener('mousedown', function(e) {
    if (currentShape === 'arrow') return; // Handle arrows separately
    
    const pos = getMousePos(e, canvas, snapSize);
    isDrawing = true;
    startX = pos.x;
    startY = pos.y;
});

document.addEventListener('mouseup', function(e) {
    if (!isDrawing) return;
    
    const pos = getMousePos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;
    
    // Only add if shape has actual size
    if (Math.abs(width) >= 10 && Math.abs(height) >= 10) {
        shapes.push({
            type: currentShape,
            x: Math.min(startX, pos.x),
            y: Math.min(startY, pos.y),
            width: Math.abs(width),
            height: Math.abs(height)
        });
        
        redrawShapes();
    }
    
    isDrawing = false;
});

document.addEventListener('mousemove', function(e) {
    if (!isDrawing) return;
    
    const pos = getMousePos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;
    
    // Redraw everything + preview
    redrawShapes();
    drawShapePreview(currentShape, startX, startY, width, height);
});

// Touch events
canvas.addEventListener('touchstart', function(e) {
    e.preventDefault();
    if (currentShape === 'arrow') return;
    
    const pos = getTouchPos(e, canvas, snapSize);
    isDrawing = true;
    startX = pos.x;
    startY = pos.y;
});

document.addEventListener('touchend', function(e) {
    if (!isDrawing) return;
    e.preventDefault();
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const touch = e.changedTouches[0];
    const x = (touch.clientX - rect.left) * scaleX;
    const y = (touch.clientY - rect.top) * scaleY;
    
    const pos = { x: snapToGrid(x, snapSize), y: snapToGrid(y, snapSize) };
    const width = pos.x - startX;
    const height = pos.y - startY;
    
    if (Math.abs(width) >= snapSize && Math.abs(height) >= snapSize) {
        shapes.push({
            type: currentShape,
            x: Math.min(startX, pos.x),
            y: Math.min(startY, pos.y),
            width: Math.abs(width),
            height: Math.abs(height)
        });
        
        redrawShapes();
    }
    
    isDrawing = false;
});

document.addEventListener('touchmove', function(e) {
    if (!isDrawing) return;
    e.preventDefault();
    
    const pos = getTouchPos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;
    
    redrawShapes();
    drawShapePreview(currentShape, startX, startY, width, height);
});

// Drawing functions
function redrawShapes() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    shapes.forEach(shape => {
        drawShape(shape.type, shape.x, shape.y, shape.width, shape.height);
    });
}

function drawShapePreview(type, x, y, width, height) {
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2;
    drawShape(type, x, y, width, height);
}

function drawShape(type, x, y, width, height) {
    switch(type) {
        case 'rectangle':
            ctx.strokeRect(x, y, width, height);
            break;
        case 'circle':
            drawCircle(x, y, width, height);
            break;
        case 'diamond':
            drawDiamond(x, y, width, height);
            break;
    }
}

function drawCircle(x, y, width, height) {
    ctx.beginPath();
    ctx.ellipse(x + width/2, y + height/2, Math.abs(width/2), Math.abs(height/2), 0, 0, 2 * Math.PI);
    ctx.stroke();
}

function drawDiamond(x, y, width, height) {
    ctx.beginPath();
    ctx.moveTo(x + width/2, y);           // top
    ctx.lineTo(x + width, y + height/2);  // right
    ctx.lineTo(x + width/2, y + height);  // bottom
    ctx.lineTo(x, y + height/2);          // left
    ctx.closePath();
    ctx.stroke();
}

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