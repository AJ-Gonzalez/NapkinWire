import { getMousePos, getTouchPos, snapToGrid } from './shared/ascii-converter.js';

const canvas = document.getElementById('diagramCanvas');
const ctx = canvas.getContext('2d');

// Touch detection for snap grid
// Better touch detection - check for actual touch capability
const isTouchDevice = ('ontouchstart' in window || navigator.maxTouchPoints > 0) && 
                     !window.matchMedia('(pointer: fine)').matches;


// Wire it up in diagram-gen.js
document.getElementById('undo-btn').addEventListener('click', function () {
    undoLastShape(
        shapes,
        () => redrawShapes(),
        () => { } // No layout update needed for diagrams
    );
});

// Show hint only when first shape is drawn
function showEditHint() {
    if (shapes.length === 1) { // First shape added
        const hint = document.createElement('div');
        hint.className = 'edit-hint';
        hint.textContent = isTouchDevice ?
            'Long press shapes to add text' :
            'Double-click shapes to add text';

        hint.style.position = 'fixed';
        hint.style.top = '20px';
        hint.style.right = '20px';
        hint.style.background = 'rgba(22, 101, 52, 0.9)';
        hint.style.color = 'white';
        hint.style.padding = '8px 12px';
        hint.style.borderRadius = '4px';
        hint.style.fontSize = '14px';
        hint.style.zIndex = '1000';
        hint.style.animation = 'fadeInOut 4s ease-in-out';

        document.body.appendChild(hint);

        // Auto-remove after 4 seconds
        setTimeout(() => hint.remove(), 4000);
    }
}

// Add this CSS for the fade animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-10px); }
        20% { opacity: 1; transform: translateY(0); }
        80% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);


const snapSize = isTouchDevice ? 15 : 10;

let currentShape = 'rectangle';
let isDrawing = false;
let startX, startY;
let shapes = []; // Store all drawn shapes

// Shape toolbar handling
document.querySelectorAll('.shape-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        // Clear all active states
        document.querySelectorAll('.shape-btn').forEach(b => b.classList.remove('active'));
        // Set this button as active
        this.classList.add('active');
        // Update current shape
        currentShape = this.dataset.shape;
    });
});

// Mouse events
canvas.addEventListener('mousedown', function (e) {

    const pos = getMousePos(e, canvas, snapSize);
    isDrawing = true;
    startX = pos.x;
    startY = pos.y;
});

document.addEventListener('mouseup', function (e) {
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
        showEditHint();
    }

    isDrawing = false;
});

document.addEventListener('mousemove', function (e) {
    if (!isDrawing) return;

    const pos = getMousePos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Redraw everything + preview
    redrawShapes();
    drawShapePreview(currentShape, startX, startY, width, height);
});

// Touch events
canvas.addEventListener('touchstart', function (e) {
    e.preventDefault();

    const pos = getTouchPos(e, canvas, snapSize);
    isDrawing = true;
    startX = pos.x;
    startY = pos.y;
});

document.addEventListener('touchend', function (e) {
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
        showEditHint();
    }

    isDrawing = false;
});

document.addEventListener('touchmove', function (e) {
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

        // Draw text if it exists
        if (shape.text) {
            ctx.fillStyle = '#333';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;
            ctx.fillText(shape.text, centerX, centerY);
        }
    });
}

function drawShapePreview(type, x, y, width, height) {
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2;
    drawShape(type, x, y, width, height);
}

function drawShape(type, x, y, width, height) {
    switch (type) {
        case 'rectangle':
            ctx.strokeStyle = '#2563eb'; // Blue - processes
            ctx.strokeRect(x, y, width, height);
            break;
        case 'circle':
            ctx.strokeStyle = '#16a34a'; // Green - start/end
            drawCircle(x, y, width, height);
            break;
        case 'diamond':
            ctx.strokeStyle = '#dc2626'; // Red - decisions
            drawDiamond(x, y, width, height);
            break;
        case 'arrow':
            ctx.strokeStyle = '#7c3aed'; // Purple - flow
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + width, y + height);
            ctx.stroke();

            // Draw arrowhead at the end point
            drawArrowhead(ctx, x + width, y + height, x, y);
            break;
    }
}

// Add this function here
function drawArrowhead(ctx, toX, toY, fromX, fromY) {
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const headlen = 15; // Length of arrowhead

    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(
        toX - headlen * Math.cos(angle - Math.PI / 6),
        toY - headlen * Math.sin(angle - Math.PI / 6)
    );
    ctx.moveTo(toX, toY);
    ctx.lineTo(
        toX - headlen * Math.cos(angle + Math.PI / 6),
        toY - headlen * Math.sin(angle + Math.PI / 6)
    );
    ctx.stroke();
}

function drawCircle(x, y, width, height) {
    ctx.beginPath();
    ctx.ellipse(x + width / 2, y + height / 2, Math.abs(width / 2), Math.abs(height / 2), 0, 0, 2 * Math.PI);
    ctx.stroke();
}

function drawDiamond(x, y, width, height) {
    ctx.beginPath();
    ctx.moveTo(x + width / 2, y);           // top
    ctx.lineTo(x + width, y + height / 2);  // right
    ctx.lineTo(x + width / 2, y + height);  // bottom
    ctx.lineTo(x, y + height / 2);          // left
    ctx.closePath();
    ctx.stroke();
}

function resizeCanvas() {
    const container = document.querySelector('.canvas-container');
    const maxWidth = Math.min(window.innerWidth - 40, 1000);
    const aspectRatio = 600 / 1000; // height/width

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


function findShapeAtPosition(x, y) {
    // Check each shape to see if point is inside
    for (let i = shapes.length - 1; i >= 0; i--) {
        const shape = shapes[i];
        if (isPointInShape(x, y, shape)) {
            return shape;
        }
    }
    return null;
}

function isPointInShape(x, y, shape) {
    switch (shape.type) {
        case 'rectangle':
            return x >= shape.x && x <= shape.x + shape.width &&
                y >= shape.y && y <= shape.y + shape.height;
        case 'circle':
            // Check if point is inside ellipse
            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;
            const radiusX = Math.abs(shape.width / 2);
            const radiusY = Math.abs(shape.height / 2);

            const dx = (x - centerX) / radiusX;
            const dy = (y - centerY) / radiusY;
            return (dx * dx + dy * dy) <= 1;

        case 'diamond':
            // Check if point is inside diamond
            const dCenterX = shape.x + shape.width / 2;
            const dCenterY = shape.y + shape.height / 2;

            const relX = Math.abs(x - dCenterX) / (shape.width / 2);
            const relY = Math.abs(y - dCenterY) / (shape.height / 2);
            return (relX + relY) <= 1;

        case 'arrow':
            // Simple line hit detection - check if near line
            return false; // Arrows don't need text for now
    }
    return false;
}

function showTextEditor(shape, clickX, clickY) {
    // Remove any existing text editor
    const existingEditor = document.querySelector('.text-editor');
    if (existingEditor) {
        existingEditor.remove();
    }

    // Create text input element
    const textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.className = 'text-editor';
    textInput.value = shape.text || ''; // Pre-fill existing text

    // Position it over the shape
    const canvasRect = canvas.getBoundingClientRect();
    const centerX = shape.x + shape.width / 2;
    const centerY = shape.y + shape.height / 2;

    textInput.style.position = 'absolute';
    textInput.style.left = (canvasRect.left + centerX - 60) + 'px'; // Center roughly
    textInput.style.top = (canvasRect.top + centerY - 10) + 'px';
    textInput.style.width = '120px';
    textInput.style.zIndex = '1000';
    textInput.style.border = '2px solid #166534';
    textInput.style.borderRadius = '4px';
    textInput.style.padding = '4px 8px';
    textInput.style.fontSize = '14px';
    textInput.style.background = 'white';

    // Add to page
    document.body.appendChild(textInput);
    textInput.focus();
    textInput.select(); // Select all text for easy editing

    // Save on Enter or blur
    function saveText() {
        shape.text = textInput.value;
        textInput.remove();
        redrawShapes(); // Redraw with new text
    }

    textInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            saveText();
        }
        if (e.key === 'Escape') {
            textInput.remove(); // Cancel without saving
        }
    });

    textInput.addEventListener('blur', saveText);
}

canvas.addEventListener('dblclick', function (e) {
    const pos = getMousePos(e, canvas, snapSize);
    const clickedShape = findShapeAtPosition(pos.x, pos.y);

    if (clickedShape) {
        showTextEditor(clickedShape, pos.x, pos.y);
    }
});

let pressTimer;

canvas.addEventListener('touchstart', function (e) {
    if (currentShape === 'text') return; // Don't interfere with drawing

    pressTimer = setTimeout(() => {
        // Long press detected
        const pos = getTouchPos(e, canvas, snapSize);
        const clickedShape = findShapeAtPosition(pos.x, pos.y);

        if (clickedShape) {
            showTextEditor(clickedShape, pos.x, pos.y);
        }
    }, 500); // 500ms long press
});

canvas.addEventListener('touchend', function (e) {
    clearTimeout(pressTimer);
});