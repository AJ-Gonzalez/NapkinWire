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
let isCurrentlyDrawing = false; // Add drawing state flag
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

// FIXED: Mouse up handler with race condition fix
document.addEventListener('mouseup', function (e) {
    if (!isDrawing) return;

    const pos = getMousePos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Cancel any pending animation frame to prevent race condition
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }

    // Clear preview immediately
    currentPreview = null;

    // Only add if shape has actual size
    if (Math.abs(width) >= 10 && Math.abs(height) >= 10) {
        if (currentShape === 'arrow') {
            shapes.push({
                type: currentShape,
                x: startX,
                y: startY,
                width: width,
                height: height
            });
        } else {
            shapes.push({
                type: currentShape,
                x: Math.min(startX, pos.x),
                y: Math.min(startY, pos.y),
                width: Math.abs(width),
                height: Math.abs(height)
            });
        }

        // Force immediate redraw instead of waiting for animation frame
        redrawShapes();
        showEditHint();
    }

    isDrawing = false;
});

// FIXED: Clean mobile touch handlers
let pressTimer;
let touchStartTime = 0;

// Helper function for touch position
function getTouchPosClean(touch, canvas, snapSize) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (touch.clientX - rect.left) * scaleX;
    const y = (touch.clientY - rect.top) * scaleY;

    return {
        x: snapToGrid(x, snapSize),
        y: snapToGrid(y, snapSize)
    };
}

canvas.addEventListener('touchstart', function (e) {
    e.preventDefault();

    const pos = getTouchPosClean(e.touches[0], canvas, snapSize);
    touchStartTime = Date.now();

    // Set up drawing state
    isDrawing = true;
    isCurrentlyDrawing = false; // Start as false, will be set to true on move
    startX = pos.x;
    startY = pos.y;

    // Set up long press timer (but not for arrows)
    if (currentShape !== 'arrow') {
        pressTimer = setTimeout(() => {
            // Only trigger if we haven't moved (still not actively drawing)
            if (!isCurrentlyDrawing) {
                const clickedShape = findShapeAtPosition(pos.x, pos.y);
                if (clickedShape) {
                    // Cancel drawing state since we're editing text
                    isDrawing = false;
                    showTextEditor(clickedShape, pos.x, pos.y);
                }
            }
        }, 500);
    }
});

document.addEventListener('touchmove', function (e) {
    if (!isDrawing) return;
    e.preventDefault();

    // Clear long press timer on move and mark as actively drawing
    clearTimeout(pressTimer);
    isCurrentlyDrawing = true;

    const pos = getTouchPosClean(e.touches[0], canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Store preview data
    currentPreview = {
        type: currentShape,
        x: startX,
        y: startY,
        width: width,
        height: height
    };

    // Throttled redraw
    if (animationFrameId) return;
    animationFrameId = requestAnimationFrame(() => {
        redrawShapes();
        if (currentPreview) {
            drawShapePreview(currentPreview.type, currentPreview.x, currentPreview.y, currentPreview.width, currentPreview.height);
        }
        animationFrameId = null;
    });
});

document.addEventListener('touchend', function (e) {
    if (!isDrawing) return;
    e.preventDefault();

    const touchDuration = Date.now() - touchStartTime;
    const wasDrawing = isCurrentlyDrawing; // Capture state before clearing

    // Clear timers
    clearTimeout(pressTimer);
    
    // If it was a very short tap (under 100ms) and we haven't moved (not actively drawing),
    // it might be intended as a text edit tap
    if (touchDuration < 100 && !wasDrawing) {
        const pos = getTouchPosClean(e.changedTouches[0], canvas, snapSize);
        const clickedShape = findShapeAtPosition(pos.x, pos.y);
        if (clickedShape) {
            showTextEditor(clickedShape, pos.x, pos.y);
            isDrawing = false;
            isCurrentlyDrawing = false;
            return;
        }
    }
    
    isCurrentlyDrawing = false;

    // Normal shape drawing logic
    const pos = getTouchPosClean(e.changedTouches[0], canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;

    if (Math.abs(width) >= snapSize && Math.abs(height) >= snapSize) {
        if (currentShape === 'arrow') {
            shapes.push({
                type: currentShape,
                x: startX,
                y: startY,
                width: width,
                height: height
            });
        } else {
            shapes.push({
                type: currentShape,
                x: Math.min(startX, pos.x),
                y: Math.min(startY, pos.y),
                width: Math.abs(width),
                height: Math.abs(height)
            });
        }
        currentPreview = null;
        redrawShapes();
        showEditHint();
    }

    isDrawing = false;
});

// Drawing functions
function redrawShapes() {
    console.trace()
    console.log('Redrawing', shapes.length, 'shapes');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    shapes.forEach(shape => {
        drawShape(shape.type, shape.x, shape.y, shape.width, shape.height);

        if (shape.text) {
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;

            // Simple text wrapping
            const maxWidth = shape.width - 8; // 4px padding on each side
            const words = shape.text.split(' ');
            const lines = [];
            let currentLine = words[0];

            for (let i = 1; i < words.length; i++) {
                const word = words[i];
                const width = ctx.measureText(currentLine + " " + word).width;
                if (width < maxWidth) {
                    currentLine += " " + word;
                } else {
                    lines.push(currentLine);
                    currentLine = word;
                }
            }
            lines.push(currentLine);

            // Draw each line
            const lineHeight = 14;
            const totalHeight = lines.length * lineHeight;
            const startY = centerY - (totalHeight / 2) + (lineHeight / 2);

            lines.forEach((line, index) => {
                ctx.fillText(line, centerX, startY + (index * lineHeight));
            });
        };
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

            // Use the parameters, not shape object
            const startX = x;
            const startY = y;
            const endX = x + width;
            const endY = y + height;

            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
            ctx.stroke();

            // Draw arrowhead at the END point
            drawArrowhead(ctx, endX, endY, startX, startY);
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
    textInput.value = shape.text || '';

    // Apply styling
    applyTextInputStyles(textInput, shape);

    document.body.appendChild(textInput);
    textInput.focus();
    textInput.select();

    // State management
    let isBeingRemoved = false;
    let popStateHandler = null;

    // Setup mobile back button handling
    if (isTouchDevice) {
        setupMobileBackButton();
    }

    function applyTextInputStyles(input, shape) {
        // Base styles - same for both platforms
        Object.assign(input.style, {
            zIndex: '9999',
            border: '2px solid #166534',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '16px',
            background: 'white',
            fontFamily: 'Arial, sans-serif',
            outline: 'none',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        });

        // Platform-specific positioning
        if (isTouchDevice) {
            // Mobile: centered overlay
            Object.assign(input.style, {
                position: 'fixed',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                width: '250px',
                maxWidth: '80vw'
            });
        } else {
            // Desktop: positioned near the shape
            positionDesktopInput(input, shape);
        }
    }

    function positionDesktopInput(input, shape) {
        const canvasRect = canvas.getBoundingClientRect();
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;

        // Scale canvas coordinates to screen coordinates
        const scaleX = canvasRect.width / canvas.width;
        const scaleY = canvasRect.height / canvas.height;

        const screenX = centerX * scaleX;
        const screenY = centerY * scaleY;

        Object.assign(input.style, {
            position: 'fixed',
            left: (canvasRect.left + screenX - 100) + 'px',
            top: (canvasRect.top + screenY - 15) + 'px',
            width: '200px',
            minWidth: '150px'
        });

        // Keep input on screen
        if (canvasRect.left + screenX + 100 > window.innerWidth - 20) {
            input.style.left = (window.innerWidth - 220) + 'px';
        }
        if (canvasRect.left + screenX - 100 < 20) {
            input.style.left = '20px';
        }
    }

    function setupMobileBackButton() {
        // Add history state for mobile back button handling
        history.pushState({ textEditorOpen: true }, '', window.location.href);

        popStateHandler = (e) => {
            if (!isBeingRemoved && document.querySelector('.text-editor')) {
                e.preventDefault();
                closeEditor();
            }
        };

        window.addEventListener('popstate', popStateHandler);
    }

    function closeEditor() {
        if (isBeingRemoved) return;
        isBeingRemoved = true;

        // Save the text
        shape.text = textInput.value;

        // Remove the input element
        if (textInput && textInput.parentNode) {
            textInput.remove();
        }

        // Clean up mobile back button handling
        if (popStateHandler) {
            window.removeEventListener('popstate', popStateHandler);
            // Only go back if we added a history state
            if (window.history.state && window.history.state.textEditorOpen) {
                history.back();
            }
        }

        // Redraw the canvas
        redrawShapes();
    }

    function cancelEditor() {
        if (isBeingRemoved) return;
        isBeingRemoved = true;

        // Remove without saving
        if (textInput && textInput.parentNode) {
            textInput.remove();
        }

        // Clean up mobile back button handling
        if (popStateHandler) {
            window.removeEventListener('popstate', popStateHandler);
            if (window.history.state && window.history.state.textEditorOpen) {
                history.back();
            }
        }
    }

    // Event handling
    textInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            closeEditor();
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            cancelEditor();
        }
    });

    textInput.addEventListener('blur', closeEditor);
}

canvas.addEventListener('dblclick', function (e) {
    const pos = getMousePos(e, canvas, snapSize);
    const clickedShape = findShapeAtPosition(pos.x, pos.y);

    if (clickedShape) {
        showTextEditor(clickedShape, pos.x, pos.y);
    }
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
                        // Skip arrows - they'll be handled as connections instead
                        continue;
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

Connections:
${generateConnections().join('\n')}`;

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

// Add these variables at the top with your other declarations
let animationFrameId = null;
let currentPreview = null;

document.addEventListener('mousemove', function (e) {
    if (!isDrawing) return;

    const pos = getMousePos(e, canvas, snapSize);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Store the preview data
    currentPreview = {
        type: currentShape,
        x: startX,
        y: startY,
        width: width,
        height: height
    };

    // Only schedule one redraw per frame (60fps max)
    if (animationFrameId) return;

    animationFrameId = requestAnimationFrame(() => {
        redrawShapes();
        if (currentPreview) {
            drawShapePreview(currentPreview.type, currentPreview.x, currentPreview.y, currentPreview.width, currentPreview.height);
        }
        animationFrameId = null;
    });
});

// Add this function to find what shape a point is touching
function findShapeAtPoint(x, y, excludeIndex = -1) {
    for (let i = shapes.length - 1; i >= 0; i--) {
        if (i === excludeIndex) continue; // Skip the arrow itself

        const shape = shapes[i];

        // Check if point is on or near the perimeter
        if (isPointNearShape(x, y, shape)) {
            return { shape, index: i };
        }
    }
    return null;
}

// Helper function to check if a point is near a shape
function isPointNearShape(x, y, shape) {
    const tolerance = 50; // pixels

    switch (shape.type) {
        case 'rectangle':
            return (x >= shape.x - tolerance && x <= shape.x + shape.width + tolerance &&
                y >= shape.y - tolerance && y <= shape.y + shape.height + tolerance) &&
                (x <= shape.x + tolerance || x >= shape.x + shape.width - tolerance ||
                    y <= shape.y + tolerance || y >= shape.y + shape.height - tolerance);

        case 'circle':
            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;
            const radiusX = Math.abs(shape.width / 2) + tolerance;
            const radiusY = Math.abs(shape.height / 2) + tolerance;

            const dx = (x - centerX) / radiusX;
            const dy = (y - centerY) / radiusY;
            return (dx * dx + dy * dy) <= 1;

        case 'diamond':
            const dCenterX = shape.x + shape.width / 2;
            const dCenterY = shape.y + shape.height / 2;
            const halfWidthTol = Math.abs(shape.width / 2) + tolerance;
            const halfHeightTol = Math.abs(shape.height / 2) + tolerance;

            const relX = Math.abs(x - dCenterX) / halfWidthTol;
            const relY = Math.abs(y - dCenterY) / halfHeightTol;
            return (relX + relY) <= 1;

        default:
            return false;
    }
}

function generateConnections() {
    let connections = [];

    shapes.forEach((shape, index) => {
        if (shape.type === 'arrow') {
            const startX = shape.x;
            const startY = shape.y;
            const endX = shape.x + shape.width;
            const endY = shape.y + shape.height;

            console.log(`Arrow ${index}: start(${startX}, ${startY}) -> end(${endX}, ${endY})`);

            const startShape = findShapeAtPoint(startX, startY, index);
            const endShape = findShapeAtPoint(endX, endY, index);

            console.log(`  Start shape:`, startShape);
            console.log(`  End shape:`, endShape);

            if (startShape && endShape) {
                const startLabel = getShapeLabel(startShape.shape, startShape.index);
                const endLabel = getShapeLabel(endShape.shape, endShape.index);

                let connection = `${startLabel} → ${endLabel}`;
                connections.push(connection);
                console.log(`  Connection: ${connection}`);
            } else {
                console.log(`  No connection found - missing start or end shape`);
            }
        }
    });

}