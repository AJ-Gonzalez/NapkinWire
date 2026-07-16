// Get mouse position relative to canvas
export function getMousePos(e, canvas, snapSize) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

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

    // Count purple shapes for numbering (matches generateASCII logic)
    let textAreaNumber = 0;

    shapes.forEach(shape => {
        if (shape.type === 'rectangle') {
            if (shape.color === '#ff00ff') { // Purple text shapes
                textAreaNumber++;

                ctx.fillStyle = shape.color;
                ctx.fillRect(shape.x, shape.y, shape.width, shape.height);

                // Draw the text area number centered on the rectangle
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 20px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(
                    textAreaNumber.toString(),
                    shape.x + shape.width / 2,
                    shape.y + shape.height / 2
                );
            } else {
                ctx.strokeStyle = shape.color;
                ctx.lineWidth = 2;
                ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
            }
        }
    });
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
    // Snapshot existing input values BEFORE clearing (keyed by field id)
    const previousValues = {};
    container.querySelectorAll('input[type="text"]').forEach(input => {
        if (input.id) previousValues[input.id] = input.value;
    });

    container.innerHTML = ''; // Clear existing fields

    let placeholderText = "e.g., Article title, User message, Navigation links";

    // Only generate fields for text areas (purple shapes)
    let textAreaCounter = 1;

    shapes.forEach((shape, index) => {
        if (shape.color === '#ff00ff') {
            const fieldDiv = document.createElement('div');
            const fieldId = `text_${index}`;
            fieldDiv.innerHTML = `
                <label>Text Area ${textAreaCounter}:</label>
                <input type="text" id="${fieldId}" placeholder="${placeholderText}">
            `;
            container.appendChild(fieldDiv);

            // Restore the previously-typed value if this field existed before
            if (previousValues[fieldId] !== undefined) {
                fieldDiv.querySelector(`#${fieldId}`).value = previousValues[fieldId];
            }

            textAreaCounter++;
        }
    });
}


export function getColorName(color) {
    const names = {
        '#ff0000': 'Red', '#00ff00': 'Green', '#4d8eff': 'Blue',
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