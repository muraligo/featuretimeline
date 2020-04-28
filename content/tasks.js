tasksmap = new Map();

class Task {
    constructor(name, txtlines) {
	this.name = name;
	this.txtlines = txtlines;
	// calculated and set fields
	this.nlines = txtlines.length;
	this.maxwidth = Task.calcMaxWidth(txtlines, this.nlines);
	this.height = 15 * this.nlines + 5
    }

    static calcMaxWidth(txtlines, nlines) {
	// calculate rectangle width based on text width
	var totallen = 0;
	var width = 0;
	for (i = 0; i < nlines; i++) {
	    var currw = txtlines[i].length * 8;
	    if (width < currw) {
		width = currw;
	    }
	}
	return width;
    }

	static drawTextBox(ctx, task, startx, starty) {
		ctx.fillStyle = "white";
		switch (task.kind) {
		case "SECURITY":
			ctx.strokeStyle = "red";
			break;
		case "COMPLIANCE":
			ctx.strokeStyle = "blue";
			break;
		case "ARCHITECTURE":
			ctx.strokeStyle = "green";
			break;
		default:
			ctx.strokeStyle = "black";
			break;
		}
		ctx.lineWidth = "1";
		ctx.strokeRect(startx, starty, task.width, task.height);
		// draw text now
		var xpos = startx + 5;
		var ypos = starty + 15;
		Task.drawUnboxedText(ctx, task.txtlines, task.nlines, xpos, ypos);
	}

    static drawUnboxedText(ctx, txtlines, nlines, startx, starty) {
	// do a for loop to draw text snippets line by line
	ctx.fillStyle = "black";
	ctx.font = "10pt sans-serif";
	var ypos = starty;
	for (i = 0; i < nlines; i++) {
	    ctx.fillText(txtlines[i], startx, ypos);
	    ypos += 15;
	}
    }
}

class TaskSet {
    constructor(jsonobj) {
	this.name = jsonobj.name;
	this.myrow = jsonobj.row;
	this.kind = jsonobj.kind;
	this.timeline_text = null;
	if (jsonobj.hasOwnProperty('timeline')) {
	    this.timeline_text = jsonobj.timeline;
        }
	this.ntasks = jsonobj.tasks.length;
	this.tasks = [];
	for (i = 0; i < this.ntasks; i++) {
	    var atask = new Task(jsonobj.tasks[i].name, jsonobj.tasks[i].textlines);
	    this.tasks.push(atask);
	}
	var npreds = jsonobj.predecessors.length;
	this.predecessors = [];
	if (jsonobj.hasOwnProperty('predecessors')) {
	    this.timeline_text = jsonobj.timeline;
            for (i = 0; i < npreds; i++) {
                this.predecessors.push(tasksmap.get(jsonobj.predecessors[i]));
            }
        }
	tasksmap.set(this.name, this);
	// calculated and set fields
	this.start_x = -1;
	this.start_y = -1;
	this.end_x = -1;
	this.end_y = -1;
	this.arrow_y = -1;
	this.timeline_y = -1;
	this.maxtxtlen = -1;
    }

    defcoords(xval, basey) {
	this.start_x = xval;
	this.timeline_y = basey + this.myrow * 100;
	this.start_y = this.timeline_y + 10;
	this.arrow_y = this.start_y + 10;
    }

	static drawArrowHead(ctx, endx, endy) {
		var arrowx = endx - 5;
		var arrowy1 = endy - 3;
		var arrowy2 = endy + 3;
		ctx.moveTo(arrowx, arrowy1);
		ctx.lineTo(endx, endy);
		ctx.stroke();
		ctx.lineTo(arrowx, arrowy2);
		ctx.stroke();
	}

	static drawLineArrow(ctx, startx, starty, endx, endy) {
		ctx.strokeStyle = "black";
		if (endy != starty) {
			var midx = startx + (endx - startx) / 2;
			ctx.moveTo(startx, starty);
			ctx.lineTo(midx, starty);
			ctx.stroke();
			ctx.lineTo(midx, endy);
			ctx.stroke();
			ctx.lineTo(endx, endy);
			ctx.stroke();
		} else {
			ctx.moveTo(startx, starty);
			ctx.lineTo(endx, endy);
			ctx.stroke();
		}
		TaskSet.drawArrowHead(ctx, endx, endy);
	}

	static drawSegmentArrow(ctx, startx, starty, midx, endx, endy) {
		ctx.strokeStyle = "black";
		ctx.moveTo(startx, starty);
		ctx.lineTo(midx, starty);
		ctx.stroke();
		ctx.lineTo(midx, endy);
		ctx.stroke();
		ctx.lineTo(endx, endy);
		ctx.stroke();
		TaskSet.drawArrowHead(ctx, endx, endy);
	}

	static drawTimeMarker(ctx, text, startx, endx, posy) {
		var totallen = text.length * 8;
		var linelen = (endx - startx - totallen) / 2;
		var midx1 = startx + linelen;
		var midx2 = endx - linelen;
		ctx.strokeStyle = "black";
		ctx.moveTo(startx, posy);
		ctx.lineTo(midx1, posy);
		ctx.stroke();
		ctx.fillStyle = "black";
		ctx.font = "10pt sans-serif";
		ctx.fillText(text, midx1 + 5, posy);
		ctx.moveTo(midx2, posy);
		ctx.lineTo(endx, posy);
		ctx.stroke();
		drawMarkerDelim(ctx, startx, posy);
		drawMarkerDelim(ctx, endx, posy);
	}

	static drawMarkerDelim(ctx, posx, posy) {
		var mystrty1 = posy - 3;
		var mystrty2 = posy + 3;
		ctx.moveTo(posx, mystrty1);
		ctx.lineTo(posx, mystrty2);
		ctx.stroke();
	}

    drawTaskSet(ctx, basex, basey) {
	var xval = basex;
	defcoords(xval, basey);
	for (i = 0; i < this.ntasks; i++) {
	    if (i != 0) {
		TaskSet.drawLineArrow(ctx, xval, this.arrow_y, xval+10, this.arrow_y);
		xval += 10;
	    }
	    Task.drawTextBox(ctx, this.tasks[i], xval, this.start_y);
	    xval += this.tasks[i].maxwidth;
	}
	TaskSet.drawTimeMarker(ctx, this.timeline_text, basex, this.timeline_y, xval, this.timeline_y);
	this.end_x = xval;
        return xval;
    }

    drawPredecessorConnections(ctx) {
        for (i = 0; i < this.predecessors.length; i++) {
	    var predx = this.predecessors[i].start_x;
	    var predy = this.predecessors[i].arrow_y;
	    TaskSet.drawLineArrow(ctx, predx, predy, this.start_x, this.arrow_y);
/*
1. Arrows from its predecessors to it
a. if in same row, straight horizontal arrow (y is same)
b. if in another row, a segmented arrow (what should be mid-x?)
3. Must know the end x positions of predecessor in row
4. Must know start and end y positions of predecessors in other rows
*/
        }
    }
}

export { Task, TaskSet };
