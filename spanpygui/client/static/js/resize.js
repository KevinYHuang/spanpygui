function manageResize(mouseDown) {
    const resizer = mouseDown.target;
    if (!resizer.classList.contains("resizer-vertical") && !resizer.classList.contains("resizer-horizontal")) {
        return;
    }

    const parent = resizer.parentNode;
    const parentStyle = getComputedStyle(parent);
    if (parentStyle.display !== "flex") {
        return;
    }

    const direction = parentStyle['flex-direction'];
    const [prev, next, sizeProp, posProp] =
        direction === 'row'            ? [resizer.previousElementSibling, resizer.nextElementSibling, "offsetWidth",  "pageX"] :
        direction === 'column'         ? [resizer.previousElementSibling, resizer.nextElementSibling, "offsetHeight", "pageY"] :
        direction === 'row-reverse'    ? [resizer.nextElementSibling, resizer.previousElementSibling, "offsetWidth",  "pageX"] :
        direction === 'column-reverse' ? [resizer.nextElementSibling, resizer.previousElementSibling, "offsetHeight", "pageY"] :
        console.error(`internal error: unimplemented resizer for ${direction}`);

    mouseDown.preventDefault();

    // Avoid cursor flickering (reset in onMouseUp)
    document.body.style.cursor = getComputedStyle(resizer).cursor;

    let prevSize = prev[sizeProp];
    let nextSize = next[sizeProp];
    let lastPos = mouseDown[posProp];

    function onMouseMove(mouseMove) {
        let pos = mouseMove[posProp];
        const d = pos - lastPos;
        prevSize += d;
        if (prevSize < 0) {
            prevSize = 0;
        }

        if (direction === 'row') {
            prev.style.width = `${prevSize}px`;
        } else {
            prev.style.height = `${prevSize}px`;
        }

        lastPos = pos;
    }

    function onMouseUp(_mouseUp) {
        // Reset cursor state that was used to avoid cursor flickering
        document.body.style.removeProperty("cursor");

        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
    }

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
}

document.body.addEventListener("mousedown", manageResize);