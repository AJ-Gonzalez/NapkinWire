import { getMousePos, getTouchPos, snapToGrid, undoLastShape, isOnPerimeter } from './shared/ascii-converter.js';

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

// Replace the showTextEditor function in diagram-gen.js with this:

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
    textInput.value = shape.text || '';

    // Base styles
    textInput.style.zIndex = '9999';
    textInput.style.border = '2px solid #166534';
    textInput.style.borderRadius = '4px';
    textInput.style.padding = '4px 8px';
    textInput.style.fontSize = '14px';
    textInput.style.background = 'white';

    // Platform-specific positioning
    if (isTouchDevice) {
        textInput.style.position = 'fixed';
        textInput.style.left = '50%';
        textInput.style.top = '50%';
        textInput.style.transform = 'translate(-50%, -50%)';
        textInput.style.width = '200px';
    } else {
        const canvasRect = canvas.getBoundingClientRect();
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;

        textInput.style.position = 'absolute';
        textInput.style.left = (canvasRect.left + centerX - 60) + 'px';
        textInput.style.top = (canvasRect.top + centerY - 10) + 'px';
        textInput.style.width = '120px';
    }

    document.body.appendChild(textInput);
    textInput.focus();
    textInput.select();

    // Define saveText function with proper scope
    function saveText() {
        shape.text = textInput.value;

        // Safe removal - check if element still exists and has a parent
        if (textInput && textInput.parentNode) {
            textInput.remove();
        }

        redrawShapes();
    }

    // Simple event handling that works on both platforms
    textInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            saveText();
        }
        if (e.key === 'Escape') {
            if (textInput && textInput.parentNode) {
                textInput.remove();
            }
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




// Add to diagram-gen.js
document.getElementById('clear-diagram').addEventListener('click', function () {
    shapes = [];
    redrawShapes();

    // Flash feedback
    const originalText = this.textContent;
    this.textContent = 'Cleared!';
    setTimeout(() => {
        this.textContent = originalText;
    }, 800);
});


function generateDiagramASCII(shapes, canvasWidth, canvasHeight, snapSize) {
    const gridWidth = Math.floor(canvasWidth / snapSize);
    const gridHeight = Math.floor(canvasHeight / snapSize);
    let asciiOutput = '';

    // Step 1: Create numbering system for shapes with text
    let shapeNumbers = new Map(); // Maps shape index -> display number
    let counter = 1;

    shapes.forEach((shape, index) => {
        // Only assign numbers to shapes that have text labels
        if (shape.text && shape.text.trim()) {
            shapeNumbers.set(index, counter++);
        }
        // Arrows and unlabeled shapes get no number (will show as connections)
    });

    // Step 2: Generate ASCII grid row by row
    for (let y = 0; y < gridHeight; y++) {
        let row = '';

        // Step 3: For each position in the row, check what should be displayed
        for (let x = 0; x < gridWidth; x++) {
            let char = ' '; // Default: empty space

            // Step 4: Check each shape to see if it touches this grid position
            for (let shapeIndex = 0; shapeIndex < shapes.length; shapeIndex++) {
                const shape = shapes[shapeIndex];

                // Step 5: Use existing perimeter detection to see if shape border is here
                if (isOnPerimeter(x, y, shape, snapSize)) {

                    // Step 6: Decide what character to show based on shape type
                    if (shape.type === 'arrow') {
                        // Arrows show as directional lines with diagonal support
                        char = getArrowChar(shape, x, y, snapSize);
                    } else if (shapeNumbers.has(shapeIndex)) {
                        // Labeled shapes show their assigned number
                        char = shapeNumbers.get(shapeIndex).toString();
                    } else {
                        // Unlabeled shapes (rare) show generic border
                        char = '#';
                    }

                    break; // Found a shape at this position, stop checking others
                }
            }

            row += char;
        }

        asciiOutput += row + '\n';
    }

    return asciiOutput;
}

// Enhanced helper function with full diagonal support
function getArrowChar(shape, gridX, gridY, snapSize) {
    const deltaX = shape.width;
    const deltaY = shape.height;

    // Calculate the angle of the arrow in degrees
    const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;

    // Choose character based on 8-directional angle ranges (45° each)
    if (angle >= -22.5 && angle < 22.5) {
        return '-';        // Horizontal right →
    } else if (angle >= 22.5 && angle < 67.5) {
        return '\\';       // Diagonal down-right ↘
    } else if (angle >= 67.5 && angle < 112.5) {
        return '|';        // Vertical down ↓
    } else if (angle >= 112.5 && angle < 157.5) {
        return '/';        // Diagonal down-left ↙
    } else if (angle >= 157.5 || angle < -157.5) {
        return '-';        // Horizontal left ←
    } else if (angle >= -157.5 && angle < -112.5) {
        return '\\';       // Diagonal up-left ↖
    } else if (angle >= -112.5 && angle < -67.5) {
        return '|';        // Vertical up ↑
    } else if (angle >= -67.5 && angle < -22.5) {
        return '/';        // Diagonal up-right ↗
    }

    return '-'; // Fallback to horizontal
}



function generateDiagramPrompt() {
    // Get the ASCII representation
    const asciiOutput = generateDiagramASCII(shapes, canvas.width, canvas.height, snapSize);

    // Build annotations for numbered shapes
    let annotations = '';
    let shapeNumbers = new Map();
    let counter = 1;

    // Assign numbers to shapes with text labels (same logic as generateDiagramASCII)
    shapes.forEach((shape, index) => {
        if (shape.text && shape.text.trim()) {
            shapeNumbers.set(index, counter++);
        }
    });

    // Create the legend
    shapes.forEach((shape, index) => {
        if (shapeNumbers.has(index)) {
            const shapeNumber = shapeNumbers.get(index);
            const shapeType = getShapeTypeDescription(shape.type);
            annotations += `${shapeNumber}: ${shape.text} (${shapeType})\n`;
        }
    });

    // Get user inputs
    const diagramType = document.getElementById('diagram-type').value || 'process';
    const additionalContext = document.getElementById('diagram-context').value;

    // Build the final prompt
    let prompt = `Here is my ${diagramType} represented as a diagram:

${asciiOutput}

Legend:
${annotations}

Arrows (-, |, \\, /) show the flow and connections between elements.`;

    if (additionalContext) {
        prompt += `\n\nAdditional context:\n${additionalContext}`;
    }

    return prompt;
}

function getShapeTypeDescription(shapeType) {
    const descriptions = {
        'rectangle': 'Process/Action',
        'diamond': 'Decision Point',
        'circle': 'Start/End Point',
        'arrow': 'Flow Direction'
    };
    return descriptions[shapeType] || 'Element';
}

// Wire up the Generate Prompt button
document.getElementById('generate-prompt').addEventListener('click', function () {
    if (shapes.length === 0) {
        // Flash feedback for empty diagram
        const originalText = this.textContent;
        this.textContent = 'Draw something first!';
        setTimeout(() => {
            this.textContent = originalText;
        }, 1500);
        return;
    }

    const prompt = generateDiagramPrompt();

    // Copy to clipboard
    navigator.clipboard.writeText(prompt).then(() => {
        // Flash success feedback
        const originalText = this.textContent;
        this.textContent = 'Copied to Clipboard!';
        this.style.backgroundColor = '#059669';

        setTimeout(() => {
            this.textContent = originalText;
            this.style.backgroundColor = 'var(--button_bg)';
        }, 1500);
    }).catch(() => {
        // Fallback if clipboard fails
        this.textContent = 'Copy failed';
        setTimeout(() => {
            this.textContent = 'Generate Prompt';
        }, 2000);
    });
});