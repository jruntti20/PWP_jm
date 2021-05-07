"use strict";

// Template from Programmable Web Project example:
// https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#full-example

// from the Programmable Web Project example
const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

// from the Programmable Web Project example
function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"];
    $("div.notification").html("<p class='error'>" + msg + "</p>");
}

// from the Programmable Web Project example
function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

// from the Programmable Web Project example
function getResource(href, renderer) {
    $.ajax({
        url: href,
        success: renderer,
        error: renderError
    });
}

function deleteResource(event, a) {
    event.preventDefault();
    let resource = $(a);
    $.ajax({
        url: resource.attr("href"),
        method: "DELETE",
        success: function () {
            var i = a.parentNode.parentNode.rowIndex;
            document.getElementById("myTable1").deleteRow(i);
        },
        error: renderError
    });
}

function deleteMember(event, a) {
    event.preventDefault();
    let resource = $(a);
    $.ajax({
        url: resource.attr("href"),
        method: "DELETE",
        success: function () {
            var i = a.parentNode.parentNode.rowIndex;
            document.getElementById("membertable").deleteRow(i);
        },
        error: renderError
    });
}

function deletePhase(event, a) {
    event.preventDefault();
    let resource = $(a);
    $.ajax({
        url: resource.attr("href"),
        method: "DELETE",
        success: function () {
            var i = a.parentNode.parentNode.rowIndex;
            document.getElementById("phasetable").deleteRow(i);
        },
        error: renderError
    });
}

// from the Programmable Web Project example
function sendData(href, method, item, postProcessor) {
    console.log(item);
    $.ajax({
        url: href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

function projectRow(item) {
    let link = "<a href='" +
                item["@controls"].self.href +
                "' onClick='followLink(event, this, renderProject)'>show</a>";
    let deleteLink = "<a href='" +
        item["@controls"].self.href +
        "' onClick='deleteResource(event, this, renderProjects)'>delete</a>";

    let start = item.start;
    if (start != null) {
        start = start.toString();
    } else {
        start = "";
    }
    let end = item.end;
    if (end != null) {
        end = end.toString();
    } else {
        end = "";
    }
    let pm = item.project_manager;
    if (pm == null) {
        pm = "";
    }

    return "<tr><td>" + item.name +
            "</td><td>" + start +
            "</td><td>" + end +
            "</td><td>" + pm +
            "</td><td>" + item.status +
            "</td><td>" + link +
            "</td><td>" + deleteLink + 
            "</td></tr>";
}

function memberRow(item) {
    let deleteLink = "<a href='" +
        item["@controls"].self.href +
        "' onClick='deleteMember(event, this, renderMembers)'>delete</a>";

    return "<tr><td>" + item.name +
        "</td><td>" + deleteLink +
        "</td></tr>";
}

function phaseRow(item) {
    let link = "<a href='" +
        item["@controls"].self.href +
        "' onClick='followLink(event, this, renderPhase)'>show</a>";
    let deleteLink = "<a href='" +
        item["@controls"].self.href +
        "' onClick='deletePhase(event, this, renderPhases)'>delete</a>";
    let dl = item.deadline;
    if (dl != null) {
        dl = dl.toString();
    } else {
        dl = "";
    }
    return "<tr><td>" + item.name +
        "</td><td>" + dl +
        "</td><td>" + item.status +
        "</td><td>" + link +
        "</td><td>" + deleteLink + 
        "</td></tr>";
}

// from the Programmable Web Project example
function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}

function appendProjectRow(body) {
    $(".resulttable tbody").append(projectRow(body));
}

function appendMemberRow(body) {
    $(".membertable tbody").append(memberRow(body));
}

function appendPhaseRow(body) {
    $(".phasetable tbody").append(phaseRow(body));
}

// from the Programmable Web Project example
function getSubmittedProject(data, status, jqxhr) {
    renderMsg("Succesful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendProjectRow);
    }
}

function getSubmittedMember(data, status, jqxhr) {
    renderMsg("Succesful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendMemberRow);
    }
}

function getSubmittedPhase(data, status, jqxhr) {
    renderMsg("Succesful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendPhaseRow);
    }
}

function renderMemberForm(ctrl) {
    let form = $("<form>");
    let name = ctrl.schema.properties.name;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitMember);
    form.append("<label>" + name.description + "</br>" +
        "<input type='text' name='name1'>" + "</label>");
    form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.memberform").html(form);
}

function renderPhaseForm(ctrl) {
    let form = $("<form>");
    let name = ctrl.schema.properties.name;
    let deadline = ctrl.schema.properties.deadline;
    let status = ctrl.schema.properties.status;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitPhase);
    form.append("<label>" + name.description + "</br>" +
        "<input type='text' name='name2'>" + "</label>");
    form.append("<label>" + deadline.description + "</br>" +
        "<input type='date' name='deadline'>" + "</label>");
    form.append("<label>" + status.description + "</br>" +
        "<select name='status2'>" +
        "<option value='NOT_STARTED'>not started</option>" +
        "<option value='STARTED'>started</option>" +
        "<option value='FINISHED'>finished</option>" +
        "</select></label></br></br>");
    var submit_text = "";
    if (ctrl.method == "POST") {
        submit_text = "Submit";
    } else {
        submit_text = "Edit";
    }
    form.append("<input type='submit' name='submit' value='" + submit_text + "'>");
    $("div.phaseform").html(form);
}

function renderProjectForm(ctrl) {
    let form = $("<form>");
    let name = ctrl.schema.properties.name;
    let start = ctrl.schema.properties.start;
    let end = ctrl.schema.properties.end;
    let project_manager = ctrl.schema.properties.project_manager;
    let status = ctrl.schema.properties.status;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitProject);
    form.append("<label>" + name.description + "</br>" +
        "<input type='text' name='name'>" + "</label>");
    form.append("<label>" + start.description + "</br>" +
        "<input type='date' name='start'>" + "</label>");
    form.append("<label>" + end.description + "</br>" +
        "<input type='date' name='end'>" + "</label>");
    form.append("<label>" + project_manager.description + "</br>" +
        "<input type='text' name='project_manager'>" + "</label>");
    form.append("<label>" + status.description + "</br>" +
        "<select name='status'>" +
        "<option value='NOT_STARTED'>not started</option>" + 
        "<option value='STARTED'>started</option>" +
        "<option value='FINISHED'>finished</option>" +
        "</select></label></br></br>");
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    var submit_text = "";
    if (ctrl.method == "POST") {
        submit_text = "Submit";
    } else {
        submit_text = "Edit";
    }
    form.append("<input type='submit' name='submit' value='" + submit_text + "'>");
    $("div.form").html(form);
}

function submitProject(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.form form");
    data.name = $("input[name='name']").val();
    if (data.name == "") {
        alert("Name can not be empty!");
        return false;
    }
    data.start = $("input[name='start']").val();
    if (data.start == "") {
        data.start = undefined;
    }
    data.end = $("input[name='end']").val();
    if (data.end == "") {
        data.end = undefined;
    }
    data.project_manager = $("input[name='project_manager']").val();
    data.status = $("select[name='status']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedProject);
}

function submitPhase(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.phaseform form");
    data.name = $("input[name='name2']").val();
    if (data.name == "") {
        alert("Name can not be empty!");
        return false;
    }
    data.deadline = $("input[name='deadline']").val();
    if (data.deadline == "") {
        data.deadline = undefined;
    }
    data.status = $("select[name='status2']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedPhase);
}

function submitMember(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.memberform form");
    data.name = $("input[name='name1']").val();
    if (data.name == "") {
        alert("Name can not be empty!");
        return false;
    }
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedMember);
}

function renderProject(body) {
    getResource("/api/projects/" + body.name + "/members/", renderProjectMembers);
    getResource("/api/projects/" + body.name + "/phases/", renderPhases);
    $("div.navigation").html(
        "<a href='" +
        body["@controls"].collection.href +
        "' onClick='followLink(event, this, renderProjects)'>collection</a>"
    );
    $("div.phases-notification").empty();

    $("#add-project").html("Edit project details");
    $("#add-member").html("Add members to project");
    $("#add-phase").html("Add new phase")
    $("#phases").html("Project phases");

    let phase = $(".phase");
    phase.show();

    let tbody = $(".resulttable tbody");
    tbody.empty();
    tbody.append("<tr><td>" + body.name +
        "</td><td>" + body.start +
        "</td><td>" + body.end +
        "</td><td>" + body.project_manager +
        "</td><td>" + body.status +
        "</td></tr>");

    renderProjectForm(body["@controls"].edit);
    $("input[name='name']").val(body.name);
    $("input[name='start']").val(body.start);
    $("input[name='end']").val(body.end);
    $("input[name='project_manager']").val(body.project_manager);
    $("input[name='status']").val(body.status);
}

function renderPhase(body) {
    $("div.phases-notification").html(
        "<a href='" +
        body["@controls"].up.href +
        "' onClick='followLink(event, this, renderProject)'>All phases</a>"
    );
    $("#add-phase").html("Edit phase");
    $("#phases").html("Phase " + body.name);

    let phase = $(".phase");
    phase.show();

    let tbody = $(".phasetable tbody");
    tbody.empty();
    tbody.append("<tr><td>" + body.name +
        "</td><td>" + body.deadline +
        "</td><td>" + body.status +
        "</td></tr>");

    renderPhaseForm(body["@controls"].edit);
    $("input[name='name2']").val(body.name);
    $("input[name='deadline']").val(body.deadline);
    $("input[name='status2']").val(body.status);
}

function renderProjects(body) {
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".resulttable thead").html(
        "<tr><th>Name</th><th>Start date</th><th>End date</th><th>Project manager</th><th>Status</th></tr>"
    );
    $("#add-project").html("Add new project");
    $("#add-member").html("Add new member");
    let phase = $(".phase");
    phase.hide();
    let tbody = $(".resulttable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(projectRow(item));
    });
    getResource("http://localhost:5000/api/members/", renderMembers);
    renderProjectForm(body["@controls"]["promana:add-project"]);
}

function renderPhases(body) {
    $(".phasetable thead").html(
        "<tr><th>Name</th><th>Deadline</th><th>Status</th></tr>"
    );
    let tbody = $(".phasetable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(phaseRow(item));
    });
    renderPhaseForm(body["@controls"]["promana:add-phase"]);
}

function renderMembers(body) {
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".membertable thead").html(
        "<tr><th>Name</th></tr>"
    );
    let tbody = $(".membertable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(memberRow(item));
    });
    renderMemberForm(body["@controls"]["promana:add-member"]);
}

function renderProjectMembers(body) {
    $(".membertable thead").html(
        "<tr><th>Name</th></tr>"
    );
    let tbody = $(".membertable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(memberRow(item));
    });
    console.log(body);
    renderMemberForm(body["@controls"]["promana:add-member"]);
}

// from the Programmable Web Project example,
// /api/sensors/ -> /api/projects/
// renderSensors -> renderProjects
$(document).ready(function () {
    getResource("http://localhost:5000/api/projects/", renderProjects);
});
