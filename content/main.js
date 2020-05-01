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
            '{"name": "UXRB2", "row": 4, "kind": "ARCHITECTURE", "timeline": "2-4 weeks", "tasks": [ { "name": "SchedUXRB2", "textlines": ["Schedule", "UXRB2"] }, { "name": "PerfUXRB2", "textlines": ["Get UXRB2", "Approval"] } ], "predecessors": ["ImplConsole"]} ' + 
            ']';
/*
		// right side at end
		drawTextBox(ctx, 'ARCHITECTURE', ['File Public SDK/CLI', 'release DEXREQ ticket', '(by Monday before GA)'], 920, 130);
		drawTimeMarker(ctx, '1-5 weeks', 915, 1265, 115);
		drawVertSegArrow(ctx, 1235, 70, 90, 1000, 130);
		drawLineArrow(ctx, 550, 230, 580, 145);
		drawTextBox(ctx, 'ARCHITECTURE', ['SDK/CLI', 'released', '(Tuesday)'], 1195, 220);
*/

var taskgraph = [];

function drawTaskGraph() {
    // load the graph
    var gphobj = JSON.parse(jsonstr);
    var i = 0;
    for (i = 0; i < gphobj.length; i++) {
        taskgraph.push(new TaskSet(gphobj[i]));
    }
    // create the canvas
    var cv = document.getElementById("mycanvas");
    var ctx = cv.getContext("2d");
    var basey = 10;
    var basex = 10;
    var nextx = basex;
    for (i = 0; i < taskgraph.length; i++) {
        nextx = taskgraph[i].drawTaskSet(ctx, nextx, basey);
        taskgraph[i].drawPredecessorConnections(ctx);
        nextx += 20;
    }
}

drawTaskGraph();

