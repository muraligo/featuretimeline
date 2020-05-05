import { Task, TaskSet } from './tasks.js';

var jsonstr = '[{"name":"ElabFeat","row":2,"kind": "SERVICE","tasks":[{"name":"ElabFeatI","textlines":["Elaborate", "Feature"]}]}, ' + 
            '{"name": "CreateSPR0", "row": 2, "kind": "ARCHITECTURE", "tasks": [ { "name": "CreateSPR1", "textlines": ["Create", "SPR"] } ], "predecessors": ["ElabFeat"]}, ' + 
            '{"name": "CreateDoc0", "row": 0, "kind": "SERVICE", "tasks": [ { "name": "CreateDoc1", "textlines": ["Create Docs", "(architecture", "feature defn", "jump page)"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "ECAReview", "row": 0, "kind": "SECURITY", "timeline": "1-2 weeks", "tasks": [ { "name": "SchedECAR", "textlines": ["Schedule", "ECAR", "Review"] }, { "name": "PerfECAR", "textlines": ["Perform", "ECAR", "Review"] } ], "predecessors": ["CreateDoc0"]}, ' + 
            '{"name": "SecurityArch", "row": 0, "kind": "SECURITY", "timeline": "1-2 weeks", "tasks": [ { "name": "SchedSecArch", "textlines": ["Schedule", "Sec Arch", "Review"] }, { "name": "PerfSecArch", "textlines": ["Get Security", "Architecture", "Approval"] } ], "predecessors": ["ECAReview"]}, ' + 
            '{"name": "SecAssmnt", "row": 1, "kind": "SECURITY", "timeline": "1 week", "tasks": [ { "name": "SubmitAssmnt", "textlines": ["Submit Svc", "Security", "Assessment"] }, { "name": "CreateCSSAP", "textlines": ["Create", "CSSAP", "Project"] }, { "name": "SubmitCSSAP", "textlines": ["Submit CSSAP", "Qualification", "Document"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "CSSAPLoBReview", "row": 0, "kind": "SECURITY", "timeline": "2-4 weeks", "tasks": [ { "name": "SchedCSSAPLoB", "textlines": ["Schedule", "CSSAP LoB", "Review"] }, { "name": "PerfCSSAPLoB", "textlines": ["Get", "CSSAP LoB", "Approval"] } ], "predecessors": ["SecurityArch", "SecAssmnt"]}, ' + 
            '{"name": "CSSAPCorpReview", "row": 0, "kind": "SECURITY", "timeline": "8-10 weeks", "tasks": [ { "name": "SchedCSSAPCorp", "textlines": ["Schedule", "CSSAP Corp", "Review"] }, { "name": "PerfCSSAPCorp", "textlines": ["Get", "CSSAP Corp", "Approval"] } ], "predecessors": ["CSSAPLoBReview"]}, ' + 
            '{"name": "SARPenTest", "row": 0, "kind": "SECURITY", "timeline": "2-3 weeks", "tasks": [ { "name": "SchedSAR", "textlines": ["Schedule", "SAR PEN", "Testing"] }, { "name": "PerfSAR", "textlines": ["Get SAR", "PEN Test", "Approval"] } ], "predecessors": ["CSSAPCorpReview"]}, ' + 
            '{"name": "CreateCPAPI0", "row": 2, "kind": "SERVICE", "timeline": "1-3 weeks", "tasks": [ { "name": "CreateCPAPI1", "textlines": ["Create Control", "Plane API", "changes PR"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "APIReview", "row": 2, "kind": "ARCHITECTURE", "timeline": "1-4 wks fast 2-8 wks slow", "tasks": [ { "name": "SchedAPIReview", "textlines": ["Kick off", "API Review"] }, { "name": "PerfAPIReview", "textlines": ["API Approved", "by Review Board"] } ], "predecessors": ["CreateCPAPI0"]}, ' + 
            '{"name": "SDKCLIReview", "row": 2, "kind": "ARCHITECTURE", "timeline": "1 week", "tasks": [ { "name": "SchedSDKCLIReview", "textlines": ["File DEXREQ ticket", "for Preview SDK/CLI", "(by Thursday)"] }, { "name": "PerfSDKCLIReview", "textlines": ["Get Preview", "SDK/CLI", "(Friday)"] } ], "predecessors": ["APIReview"]}, ' + 
            '{"name": "SDKCLIExamples", "row": 2, "kind": "SERVICE", "tasks": [ { "name": "SDKCLITests", "textlines": ["Create", "SDK/CLI", "tests and", "examples"] } ], "predecessors": ["SDKCLIReview"]}, ' + 
            '{"name": "ImplFeature", "row": 3, "kind": "SERVICE", "tasks": [ { "name": "ImplFeat1", "textlines": ["Implement", "Feature", "(deploy to", " PHX and IAD)"] } ], "predecessors": ["APIReview"]}, ' + 
            '{"name": "TFReview", "row": 3, "kind": "ARCHITECTURE", "timeline": "2-4 weeks", "tasks": [ { "name": "PerfTFReview", "textlines": ["Work on TER", "ticket to start", "TF Preview", "(Monday)"] }, { "name": "TestTF", "textlines": ["TF tests", "pass"] } ], "predecessors": ["ImplFeature"]}, ' + 
            '{"name": "PABReview", "row": 3, "kind": "ARCHITECTURE", "timeline": "4-6 weeks", "tasks": [ { "name": "SchedPABReview", "textlines": ["Schedule", "PAB", "Review"] }, { "name": "PerfPABReview", "textlines": ["PAB", "Review", "Done"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "UXDesign", "row": 4, "kind": "SERVICE", "timeline": "2-3 weeks", "tasks": [ { "name": "CreateUX", "textlines": ["Work with", "UX Designer"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "UXRB1", "row": 4, "kind": "ARCHITECTURE", "timeline": "2-4 weeks", "tasks": [ { "name": "SchedUXRB1", "textlines": ["Schedule", "UXRB1"] }, { "name": "PerfUXRB1", "textlines": ["Get UXRB1", "Approval"] } ], "predecessors": ["UXDesign"]}, ' + 
            '{"name": "ImplConsole", "row": 4, "kind": "SERVICE", "tasks": [ { "name": "ImplConsol1", "textlines": ["Implement", "Console", "(deploy to", "Prod)"] } ], "predecessors": ["UXRB1"]}, ' + 
            '{"name": "UXRB2", "row": 4, "kind": "ARCHITECTURE", "timeline": "2-4 weeks", "tasks": [ { "name": "SchedUXRB2", "textlines": ["Schedule", "UXRB2"] }, { "name": "PerfUXRB2", "textlines": ["Get UXRB2", "Approval"] } ], "predecessors": ["ImplConsole"]}, ' + 
            '{"name": "ContentReview", "row": 5, "kind": "ARCHITECTURE", "timeline": "2-4 weeks", "tasks": [ { "name": "TechContentReview", "textlines": ["Engage with", "Technical", "Content team"] }, { "name": "CmpltTCReview", "textlines": ["Technical", "Content", "Done"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "TrainReview", "row": 6, "kind": "SERVICE", "timeline": "4-5 weeks", "tasks": [ { "name": "SchedTraining", "textlines": ["Schedule Customer", "Support Training"] }, { "name": "PerfTraining", "textlines": ["Train", "Customer Support"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "ComplyOpsReady", "row": 7, "kind": "SERVICE", "tasks": [ { "name": "OpsReadiness", "textlines": ["Work on Ops", "Readiness", "Requirements"] }, { "name": "Compliance", "textlines": ["Work on", "Compliance", "Requirements"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "PlatformBarApproval", "row": 7, "kind": "COMPLIANCE", "timeline": "3-4 weeks (incl RQS impact)", "tasks": [ { "name": "PerfPlatformBar", "textlines": ["Work on", "Platform Bar", "Requirements"] }, { "name":"GetPlatformBar", "textlines":["Platform Bar", "Validated"] } ], "predecessors": ["ComplyOpsReady"]}, ' + 
            '{"name": "3rdpartyApproval", "row": 8, "kind": "COMPLIANCE", "timeline": "1-8 weeks", "tasks": [ { "name": "File3rdPartyApprove", "textlines": ["File 3rd Party", "Approvals"] }, { "name":"GetFile3rdPartyApprove", "textlines":["Get 3rd Party", "Approvals"] } ], "predecessors": ["CreateSPR0"]}, ' + 
            '{"name": "SecurityUpdates", "row": 8, "kind": "COMPLIANCE", "timeline": "1-2 weeks", "tasks": [ { "name": "SecUpdate1", "textlines": ["Security Updates -", "Static Code Analysis", "DASS, Malware scan,", "Sonatype scan"] } ], "predecessors": ["3rdpartyApproval"]}, ' + 
            '{"name": "SDKCLIRelease1", "row": 2, "kind": "ARCHITECTURE", "tasks": [ { "name": "SchedSDKCLIRelease", "textlines": ["File Public SDK/CLI", "release DEXREQ ticket", "(by Mon b/f GA)"] } ], "predecessors": ["SDKCLIExamples"]}, ' + 
            '{"name": "GARMApproval", "row": 3, "kind": "ARCHITECTURE", "tasks": [ { "name": "UDXGAApprove", "textlines": ["UDX GA Approval", "Decision made (by", "Thursday before GA)", "(must GA after this)"] }, { "name": "RMApprove", "textlines": ["Get OCI RM", "Approval"] } ], "predecessors": ["SDKCLIRelease1", "TFReview", "UXRB2", "ContentReview"]}, ' + 
            '{"name": "SDKCLIRelease2", "row": 2, "kind": "ARCHITECTURE", "tasks": [ { "name": "PerfSDKCLIRelease", "textlines": ["SDK/CLI", "released", "(Tuesday)"] } ], "predecessors": ["GARMApproval"]}, ' + 
            '{"name": "TFRelease", "row": 3, "kind": "ARCHITECTURE", "tasks": [ { "name": "PerfTFRelease", "textlines": ["Terraform", "released", "(Wednesday)"] } ], "predecessors": ["GARMApproval"]}, ' + 
            '{"name": "ConsoleRelease", "row": 5, "kind": "ARCHITECTURE", "tasks": [ { "name": "TechConsoleRelease", "textlines": ["Console", "Technical", "Content", "released", "(Tuesday)"] } ], "predecessors": ["GARMApproval"]}, ' + 
            '{"name": "FeatureGA", "row": 3, "kind": "SERVICE", "tasks": [ { "name": "PerfGA", "textlines": ["Feature", "GA"] } ], "predecessors": ["TFRelease", "SDKCLIRelease2", "ConsoleRelease"]} ' + 
            ']';

function drawLegend(ctx) {
    ctx.fillStyle = "white";
    ctx.strokeStyle = "black";
    ctx.strokeRect(10, 10, 56, 20);
    ctx.fillStyle = "black";
    ctx.fillText('General', 15, 25);
    ctx.fillStyle = "white";
    ctx.strokeStyle = "green";
    ctx.strokeRect(10, 35, 96, 20);
    ctx.fillStyle = "black";
    ctx.fillText('Architecture', 15, 50);
    ctx.fillStyle = "white";
    ctx.strokeStyle = "blue";
    ctx.strokeRect(10, 60, 80, 20);
    ctx.fillStyle = "black";
    ctx.fillText('Compliance', 15, 75);
    ctx.fillStyle = "white";
    ctx.strokeStyle = "red";
    ctx.strokeRect(10, 85, 64, 20);
    ctx.fillStyle = "black";
    ctx.fillText('Security', 15, 100);
}

function drawVertArrowHead(ctx, dirn, endx, endy) {
    var arrowy = endy;
    if (dirn < 0) { // UP
        arrowy += 5;
    } else {
        arrowy -= 5;
    }
    var arrowx1 = endx - 3;
    var arrowx2 = endx + 3;
    ctx.moveTo(arrowx1, arrowy);
    ctx.lineTo(endx, endy);
    ctx.stroke();
    ctx.lineTo(arrowx2, arrowy);
    ctx.stroke();
}

function drawUpVertArrow(ctx, startx, starty, endx, endy) {
    ctx.strokeStyle = "black";
    ctx.moveTo(startx, starty);
    ctx.lineTo(endx, starty);
    ctx.stroke();
    ctx.lineTo(endx, endy);
    ctx.stroke();
    drawVertArrowHead(ctx, (endy - starty), endx, endy);
}

function drawSarToSDKCLIRel(ctx) {
    var taskset = TaskSet.getTaskSetByName("SARPenTest");
    var sarx1 = taskset.start_x + 20;
    var sary1 = taskset.start_y + taskset.tasks[1].height;
    var sary2 = sary1 + 20;
    taskset = TaskSet.getTaskSetByName("SDKCLIRelease1");
    var sdkx1 = taskset.start_x + 40;
    var sdky1 = taskset.start_y;
    ctx.strokeStyle = "black";
    ctx.moveTo(sarx1, sary1);
    ctx.lineTo(sarx1, sary2);
    ctx.stroke();
    ctx.lineTo(sdkx1, sary2);
    ctx.stroke();
    ctx.lineTo(sdkx1, sdky1);
    ctx.stroke();
    drawVertArrowHead(ctx, (sdky1 - sary1), sdkx1, sdky1);
}

function drawPabToGarm(ctx) {
    var taskset = TaskSet.getTaskSetByName("GARMApproval");
    var garmx1 = taskset.start_x;
    taskset = TaskSet.getTaskSetByName("PABReview");
    var pabx1 = taskset.end_x;
    var paby1 = taskset.arrow_y;
    var pabx2 = pabx1 + 20;
    var paby2 = taskset.start_y - 20;
    var pabx3 = garmx1 - 20;
    ctx.strokeStyle = "black";
    ctx.moveTo(pabx1, paby1);
    ctx.lineTo(pabx2, paby1);
    ctx.stroke();
    ctx.lineTo(pabx2, paby2);
    ctx.stroke();
    ctx.lineTo(pabx3, paby2);
    ctx.stroke();
    ctx.lineTo(garmx1, paby1);
    ctx.stroke();
    TaskSet.drawArrowHead(ctx, garmx1, paby1)
}

var taskgraph = [];

function drawTaskGraph() {
    // load the graph
    var gphobj = JSON.parse(jsonstr);
    var i = 0;
    for (i = 0; i < gphobj.length; i++) {
        taskgraph.push(new TaskSet(gphobj[i]));
    }
    // draw legend in the canvas
    var cv = document.getElementById("mycanvas");
    var ctx = cv.getContext("2d");
    ctx.lineWidth = "1";
    ctx.font = "10pt sans-serif";
    drawLegend(ctx);
    // draw graph in the canvas
    var basey = 40;
    var basex = 10;
    var nextx = basex;
    for (i = 0; i < taskgraph.length; i++) {
        nextx = taskgraph[i].drawTaskSet(ctx, nextx, basey);
        taskgraph[i].drawPredecessorConnections(ctx);
        nextx += 20;
    }
    TaskSet.drawSeparateTimeMarker(ctx, '1.5 weeks', "SDKCLIRelease1", "SDKCLIRelease2", 2, basey);
    drawSarToSDKCLIRel(ctx);
    drawPabToGarm(ctx);
    var taskset = TaskSet.getTaskSetByName("GARMApproval");
    var garmx1 = taskset.end_x;
    var garmy1 = taskset.start_y + taskset.tasks[1].height;
//    taskset = TaskSet.getTaskSetByName("TrainReview");
/*
		// right side at end; separate timeline above row2; separate arrow from SAR PEN Test Approval to File Public SDK/CLI
		drawTimeMarker(ctx, '1-5 weeks', 915, 1265, 115);
		drawVertSegArrow(ctx, 1235, 70, 90, 1000, 130);
	    // draw bent vertical arrows from Customer Support down all to OCI RM Approval
*/

}

drawTaskGraph();

