"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"];
    $("div.notification").html("<p class='error'>" + msg + "</p>");
}

function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

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

function sendData(href, method, item, postProcessor) {
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

function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}

function appendProjectRow(body) {
    $(".resulttable tbody").append(projectRow(body));
}

function getSubmittedProject(data, status, jqxhr) {
    renderMsg("Successful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendProjectRow);
    }
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
    form.append("<label>" + name.description + "</label>");
    form.append("<input type='text' name='name'>");
    form.append("<label>" + start.description + "</label>");
    form.append("<input type='text' name='start'>");
    form.append("<label>" + end.description + "</label>");
    form.append("<input type='text' name='end'>");
    form.append("<label>" + project_manager.description + "</label>");
    form.append("<input type='text' name='project_manager'>");
    form.append("<label>" + status.description + "</label>");
    form.append("<input type='text' name='status'>");
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.form").html(form);
}

function submitProject(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.form form");
    data.name = $("input[name='name']").val();
    data.start = $("input[name='start date']").val();
    data.end = $("input[name='end date']").val();
    data.project_manager = $("input[name='manager']").val();
    data.status = $("input[name='status']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedProject);
}

function renderProject(body) {
    $("div.navigation").html(
        "<a href='" +
        body["@controls"].collection.href +
        "' onClick='followLink(event, this, renderProjects)'>collection</a>"
    );
    $(".resulttable thead").empty();
    $(".resulttable tbody").empty();
    $("input[name='name']").val(body.name);
    $("input[name='start']").val(body.start);
    $("input[name='end']").val(body.end);
    $("input[name='project_manager']").val(body.project_manager);
    $("form input[type='submit']").before(
        "<label>Status</label>" +
        "<input type='text' name='status' value='" +
        body.status + "' readonly>"
    );
}

function renderProjects(body) {
    console.log(body);
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".resulttable thead").html(
        "<tr><th>Name</th><th>Start date</th><th>End date</th><th>Project manager</th><th>Status</th></tr>"
    );
    let tbody = $(".resulttable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(projectRow(item));
    });
    renderProjectForm(body["@controls"]["promana:add-project"]);
}

$(document).ready(function () {
    getResource("http://localhost:5000/api/projects/", renderProjects);
});
