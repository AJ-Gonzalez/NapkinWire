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

// New function that handles both ASCII and input field generation:
function updateLayout() {
    const ascii_out = generateASCII();
    document.getElementById('ascii-preview').textContent = ascii_out;
    generateInputFields();
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
    if (shape.type === 'rectangle') {
        const pixelX = x * snapSize;
        const pixelY = y * snapSize;

        const onLeftOrRight = (pixelX === shape.x || pixelX === shape.x + shape.width - snapSize) &&
            (pixelY >= shape.y && pixelY < shape.y + shape.height);
        const onTopOrBottom = (pixelY === shape.y || pixelY === shape.y + shape.height - snapSize) &&
            (pixelX >= shape.x && pixelX < shape.x + shape.width);

        return onLeftOrRight || onTopOrBottom;
    }

    // TODO: Add diamond, circle, arrow logic later
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


export function generateFinalPrompt() {
    const asciiLayout = generateASCII();
    const overallPurpose = document.getElementById('overall-purpose').value || 'web interface';
    const platform = document.getElementById('platform').value || 'vanilla JS';
    const isTUI = document.getElementById("tuiMode").checked;

    // Build create statement
    let createStatement = '';
    if (isTUI) {
        createStatement = `Create this TUI (Terminal User Interface) using ${platform}`;
    } else {
        createStatement = `Create this GUI using ${platform}`;
    }

    // Collect only text area descriptions
    let textAreaDescriptions = '';
    let textAreaCounter = 1;

    shapes.forEach((rect, index) => {
        if (rect.color === '#ff00ff') {
            const textInput = document.getElementById(`text_${index}`);
            const description = textInput ? textInput.value : 'text content';
            textAreaDescriptions += `\nText Area ${textAreaCounter}: ${description}`;
            textAreaCounter++;
        }
    });

    // Build final prompt
    let finalPrompt = `${createStatement}, it will be used for a ${overallPurpose}

Using the following layout:

${asciiLayout}

Content areas:${textAreaDescriptions}

Please create a functional interface that matches this layout exactly. Use the visual structure shown in the ASCII art as your guide for positioning and proportions.`;


    return finalPrompt;
}


export function snapToGrid(coord, snapSize) {
    return Math.floor(coord / snapSize) * snapSize;
}