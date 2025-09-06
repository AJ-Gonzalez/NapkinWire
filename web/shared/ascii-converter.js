// Get mouse position relative to canvas
export function getMousePos(e, canvas, snapSize) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const rawX = e.clientX - rect.left;
    const rawY = e.clientY - rect.top;
    const x = rawX * scaleX;
    const y = rawY * scaleY;

    // Debug logging for deadzone investigation
    if (Math.random() < 0.01) { // Log 1% of mouse events to avoid spam
        console.log('Mouse debug:', {
            clientX: e.clientX,
            clientY: e.clientY,
            rectLeft: rect.left,
            rectTop: rect.top,
            rectWidth: rect.width,
            rectHeight: rect.height,
            canvasWidth: canvas.width,
            canvasHeight: canvas.height,
            scaleX: scaleX,
            scaleY: scaleY,
            rawX: rawX,
            rawY: rawY,
            scaledX: x,
            scaledY: y,
            snappedX: snapToGrid(x, snapSize),
            snappedY: snapToGrid(y, snapSize)
        });
    }

    return {
        x: snapToGrid(x, snapSize),
        y: snapToGrid(y, snapSize)
    };
}


export function getTouchPos(e, canvas, snapSize) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const touch = e.touches[0]; // First finger
    const x = (touch.clientX - rect.left) * scaleX;
    const y = (touch.clientY - rect.top) * scaleY;

    return {
        x: snapToGrid(x, snapSize),
        y: snapToGrid(y, snapSize)
    };
}


export function undoLastShape(shapes, redrawCallback, updateCallback) {
    if (shapes.length > 0) {
        shapes.pop();
        redrawCallback();
        updateCallback();
    }
}

export function updateLayout(shapes, canvasWidth, canvasHeight, snapSize, colorMapping, asciiElement, inputContainer, role) {
    const asciiOutput = generateASCII(shapes, canvasWidth, canvasHeight, snapSize, colorMapping);
    asciiElement.textContent = asciiOutput;
    generateInputFields(shapes, inputContainer, role);
}

export function redrawCanvas(ctx, shapes) {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    shapes.forEach(shape => {
        if (shape.type === 'rectangle') {
            if (shape.color === '#ff00ff') { // Purple text shapes
                ctx.fillStyle = shape.color;
                ctx.fillRect(shape.x, shape.y, shape.width, shape.height);
            } else {
                ctx.strokeStyle = shape.color;
                ctx.lineWidth = 2;
                ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
            }
        }
        // Add handling for other shape types later
    }
    );
}

export function isOnPerimeter(x, y, shape, snapSize) {
    const pixelX = x * snapSize;
    const pixelY = y * snapSize;

    if (shape.type === 'rectangle') {
        const onLeftOrRight = (pixelX === shape.x || pixelX === shape.x + shape.width - snapSize) &&
            (pixelY >= shape.y && pixelY < shape.y + shape.height);
        const onTopOrBottom = (pixelY === shape.y || pixelY === shape.y + shape.height - snapSize) &&
            (pixelX >= shape.x && pixelX < shape.x + shape.width);

        return onLeftOrRight || onTopOrBottom;
    }

    if (shape.type === 'circle') {
        // Check if point is on the ellipse perimeter
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        const radiusX = Math.abs(shape.width / 2);
        const radiusY = Math.abs(shape.height / 2);

        const dx = (pixelX - centerX) / radiusX;
        const dy = (pixelY - centerY) / radiusY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Check if we're close to the perimeter (within one grid cell)
        const tolerance = snapSize / Math.max(radiusX, radiusY);
        return Math.abs(distance - 1) <= tolerance;
    }

    if (shape.type === 'diamond') {
        // Check if point is on diamond perimeter
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        const halfWidth = shape.width / 2;
        const halfHeight = shape.height / 2;

        const relX = Math.abs(pixelX - centerX) / halfWidth;
        const relY = Math.abs(pixelY - centerY) / halfHeight;
        
        // Check if we're close to the diamond edge (relX + relY = 1)
        const edgeDistance = Math.abs((relX + relY) - 1);
        const tolerance = snapSize / Math.max(halfWidth, halfHeight);
        return edgeDistance <= tolerance;
    }

    if (shape.type === 'arrow') {
        // Check if point is close to the line segment
        const startX = shape.x;
        const startY = shape.y;
        const endX = shape.x + shape.width;
        const endY = shape.y + shape.height;

        // Calculate distance from point to line segment
        const lineLength = Math.sqrt(shape.width * shape.width + shape.height * shape.height);
        if (lineLength === 0) return false; // Zero-length arrow

        // Vector from start to end
        const lineX = shape.width / lineLength;
        const lineY = shape.height / lineLength;

        // Vector from start to point
        const pointX = pixelX - startX;
        const pointY = pixelY - startY;

        // Project point onto line
        const projection = (pointX * lineX + pointY * lineY);
        
        // Clamp projection to line segment
        const clampedProjection = Math.max(0, Math.min(lineLength, projection));
        
        // Find closest point on line segment
        const closestX = startX + clampedProjection * lineX;
        const closestY = startY + clampedProjection * lineY;
        
        // Calculate distance from point to closest point on line
        const distance = Math.sqrt(
            (pixelX - closestX) * (pixelX - closestX) + 
            (pixelY - closestY) * (pixelY - closestY)
        );
        
        // Point is "on" the arrow if within half a grid cell of the line
        return distance <= snapSize / 2;
    }

    return false;
}

export function generateASCII(shapes, canvasWidth, canvasHeight, snapSize, colorMapping) {

    const gridWidth = Math.floor(canvasWidth / snapSize);
    const gridHeight = Math.floor(canvasHeight / snapSize);
    let asciiOutput = '';

    // Track text areas for numbering
    let textAreaCounter = 1;
    const textAreaNumbers = new Map(); // rect index -> number

    // Assign numbers to text areas first
    shapes.forEach((shape, index) => {
        if (shape.color === '#ff00ff') {
            textAreaNumbers.set(index, textAreaCounter++);
        }
    });

    for (let y = 0; y < gridHeight; y++) {
        let row = '';
        for (let x = 0; x < gridWidth; x++) {
            let char = ' '; // default empty space

            for (let shapeIndex = 0; shapeIndex < shapes.length; shapeIndex++) {
                const shape = shapes[shapeIndex];

                if (isOnPerimeter(x, y, shape, snapSize)) {
                    if (shape.color === '#ff00ff') {
                        // Use the assigned number for this text area
                        char = textAreaNumbers.get(shapeIndex).toString();
                    } else {
                        char = colorMapping[shape.color] || '?';
                    }
                    break;
                }
            }
            row += char;
        }
        asciiOutput += row + '\n';
    }

    return asciiOutput;
}

export function generateInputFields(shapes, container, role) {
    container.innerHTML = ''; // Clear existing fields

    let placeholderText = "e.g., Text content";  // Default

    if (role === "UI") {
        placeholderText = "e.g., Article title, User message, Navigation links";
    } else if (role === "diagram") {
        placeholderText = "e.g., Process step, Decision point, Data flow";
    }

    // Only generate fields for text areas (purple shapes)
    let textAreaCounter = 1;

    shapes.forEach((shape, index) => {
        if (shape.color === '#ff00ff') {
            const fieldDiv = document.createElement('div');
            fieldDiv.innerHTML = `
                <label>Text Area ${textAreaCounter}:</label>
                <input type="text" id="text_${index}" placeholder="${placeholderText}">
            `;
            container.appendChild(fieldDiv);
            textAreaCounter++;
        }
    });
}


export function getColorName(color) {
    const names = {
        '#ff0000': 'Red', '#00ff00': 'Green', '#0000ff': 'Blue',
        '#DAA520': 'Yellow', '#ff00ff': 'Purple'
    };
    return names[color] || 'Unknown';
}

/**
 * Generates ASCII layout with text annotations from input fields
 * @param {string} asciiLayout - The ASCII art layout
 * @param {Array} shapes - Array of shape objects
 * @param {HTMLElement} inputContainer - Container element with text inputs
 * @param {string} - Context, e.g. Content areas, Diagram block text
 * @returns {string} Formatted ASCII with annotations
 */
export function generateAnnotatedASCII(asciiLayout, shapes, inputContainer, annotationContext) {
    let textAreaDescriptions = '';
    let textAreaCounter = 1;

    shapes.forEach((shape, index) => {
        if (shape.color === '#ff00ff') {
            const textInput = inputContainer.querySelector(`#text_${index}`);
            const description = textInput ? textInput.value : 'text content';
            textAreaDescriptions += `\nText Area ${textAreaCounter}: ${description}`;
            textAreaCounter++;
        }
    });

    // Build final prompt
    let finalPrompt = `
${asciiLayout}


${annotationContext}:${textAreaDescriptions}
`
    return finalPrompt;
}


export function snapToGrid(coord, snapSize) {
    return Math.floor(coord / snapSize) * snapSize;
}