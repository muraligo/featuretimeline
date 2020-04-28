import { Task, TaskSet } from './tasks.js';

var jsonstr = '[{"name":"ElabFeat","row":1,"kind": "SERVICE","tasks":[{"name":"ElabFeatI","textlines":["Elaborate", "Feature"]}]}, {"name": "CreateSPR0", "row": 1, "kind": "ARCHITECTURE", "tasks": [ { "name": "CreateSPR1", "textlines": ["Create", "SPR"] } ], "predecessors": ["ElabFeat"]}, {"name": "CreateDoc0", "row": 0, "kind": "SERVICE", "tasks": [ { "name": "CreateDoc1", "textlines": ["Create Docs", "(architecture", "feature defn", "jump page)"] } ], "predecessors": ["CreateSPR0"]}, {"name": "ECAR", "row": 0, "kind": "SECURITY", "timeline": "2 weeks", "tasks": [ { "name": "SchedECAR", "textlines": ["Schedule", "ECAR", "Review"] }, { "name": "PerfECAR", "textlines": ["Perform", "ECAR", "Review"] } ], "predecessors": ["CreateDoc0"]} ]';

var taskgraph = [];

function loadTaskGraph() {
	var gphobj = JSON.parse(jsonstr);
	for (i = 0; i < gphobj.length; i++) {
		taskgraph.push(new TaskSet(gphobj[i]));
	}
}

function drawTaskGraph() {
    // create the canvas
    var cv = document.getElementById("mycanvas");
    var ctx = cv.getContext("2d");
    var basey = 10;
    var basex = 10;
    var nextx = basex;
    for (i = 0; i < taskgraph.length; i++) {
        nextx = taskgraph[i].drawTaskSet(ctx, nextx, basey);
        taskgraph[i].drawPredecessorConnections(ctx);
    }
}
