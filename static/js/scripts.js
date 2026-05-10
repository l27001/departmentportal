function openModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

// Функция для закрытия модального окна
function closeModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

// Закрытие модального окна при клике за его пределами
window.onclick = function(event) {
  var modals = document.getElementsByClassName("modal");
  for (var i = 0; i < modals.length; i++) {
    if (event.target == modals[i]) {
      modals[i].style.display = "none";
    }
  }
}

function togglePw(id, btn) {
  var input = document.getElementById(id);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}

function updateTaskStatus(el, id) {
    var taskItem = el.closest('.task-item');
    var newVal = el.value;
    var fromModal = !taskItem;
    fetch(`/api/tasks/${id}/status`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ status: newVal }),
    })
    .then(function(response){
        return response.json()
    })
    .then(function(result){
        console.log(result)
        if (!taskItem) {
            taskItem = document.querySelector('.task-item[data-task-id="' + id + '"]');
        }
        if (newVal === 'Завершена') {
            if (taskItem) {
                taskItem.classList.add('task-completed');
                taskItem.classList.remove('task-review');
            }
        } else if (newVal === 'На проверке') {
            if (taskItem) {
                taskItem.classList.add('task-review');
                taskItem.classList.remove('task-completed');
            }
        } else {
            if (taskItem) {
                taskItem.classList.remove('task-completed');
                taskItem.classList.remove('task-review');
            }
        }
        if (taskItem) {
            taskItem.querySelectorAll('select').forEach(function(s) {
                for (var i = 0; i < s.options.length; i++) {
                    if (s.options[i].text === newVal) {
                        s.selectedIndex = i;
                        break;
                    }
                }
            });
        }
        var modal = document.getElementById('taskDetailsModal');
        if (modal && modal.style.display === 'block') {
            openTaskDetails(id);
        }
    })
}

function openAnnouncement(id, roleId) {
  document.getElementById('announcementModalTitle').textContent = '';
  document.getElementById('announcementModalMeta').innerHTML = '';
  document.getElementById('announcementModalText').innerHTML = '';
  document.getElementById('announcementModalAttachments').innerHTML = '';
  document.getElementById('announcementReadStatus').innerHTML = '';
  document.getElementById('announcementRsvpSection').innerHTML = '';
  fetch(`/api/announcements/${id}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById('announcementModalTitle').textContent = data.title;
    var parts = data.deadline.split('T')[0].split('-');
    var formattedDate = parts[2] + '.' + parts[1] + '.' + parts[0];
    document.getElementById('announcementModalMeta').innerHTML =
      '<span class="meta-badge meta-deadline"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>Срок: ' + formattedDate + '</span>' +
      '<span class="meta-badge meta-author"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' + (data.creator_name || '—') + '</span>';
    document.getElementById('announcementModalText').innerHTML = '<p>' + data.text.replace(/\n/g, '<br>') + '</p>';
    fetch(`/api/announcements/${id}/attachments`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    })
    .then(r => r.json())
    .then(files => {
      var cont = document.getElementById('announcementModalAttachments');
      if (files.length > 0) {
        cont.innerHTML = '<div class="modal-attachments-section"><h4><svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>Вложения</h4>' +
          files.map(f => '<a href="/api/attachments/' + f.id + '" target="_blank" class="modal-attachment-link"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' + f.file_name + '</a>').join('') +
          '</div>';
      } else {
        cont.innerHTML = '';
      }
    });
    if (data.require_rsvp) {
      loadRsvpSection(id, roleId);
    } else {
      document.getElementById('announcementRsvpSection').innerHTML = '';
    }
    openModal('announcementModal');
    fetch(`/api/announcements/${id}/view`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    }).then(() => {
      var el = document.querySelector('.announcement-all-card[data-id="' + id + '"]') ||
               document.querySelector('.announcement-card[data-id="' + id + '"]');
      if (el) {
        el.classList.remove('unread');
        var dot = el.querySelector('.unread-dot');
        if (dot) dot.remove();
        var header = el.querySelector('.announcement-all-header') || el.querySelector('.announcement-card-header');
        if (header && !header.querySelector('.announcement-read-check')) {
          header.innerHTML += '<svg class="announcement-read-check" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        }
      }
    });
    if (roleId === 1 || roleId === 2) {
      fetch(`/api/announcements/${id}/read-status`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
      .then(r => {
        if (!r.ok) {
          document.getElementById('announcementReadStatus').innerHTML = '';
          return null;
        }
        return r.json();
      })
      .then(data => {
        if (!data) return;
        var statusDiv = document.getElementById('announcementReadStatus');
        var html = '<div class="read-status-section"><h4>Прочитано</h4><div class="read-status-grid">';
        data.read.forEach(function(u) {
          html += '<div class="read-status-card read"><span class="read-status-name">' + u.user_name + '</span><span class="read-status-badge">Прочитано</span></div>';
        });
        html += '</div><h4>Не прочитано</h4><div class="read-status-grid">';
        data.unread.forEach(function(u) {
          html += '<div class="read-status-card unread"><span class="read-status-name">' + u.user_name + '</span><span class="read-status-badge">Не прочитано</span></div>';
        });
        html += '</div></div>';
        statusDiv.innerHTML = html;
      });
    }
  });
}

var currentRsvpAnnouncementId = null;
var currentAnnouncementRoleId = null;

function loadRsvpSection(id, roleId) {
  currentRsvpAnnouncementId = id;
  currentAnnouncementRoleId = roleId;
  var div = document.getElementById('announcementRsvpSection');
  fetch(`/api/announcements/${id}/rsvp`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })
  .then(r => r.json())
  .then(status => {
    var btnText = status.rsvped ? '✅ Отмечено' : '☐ Отметить участие';
    var btnClass = status.rsvped ? 'rsvp-btn active' : 'rsvp-btn';
    var html = '<div class="rsvp-section"><div class="rsvp-header"><span class="rsvp-count">' + status.rsvp_count + ' ' + pluralize(status.rsvp_count, 'отметка', 'отметки', 'отметок') + '</span></div><div class="rsvp-actions"><button class="' + btnClass + '" onclick="toggleRsvp(' + id + ')">' + btnText + '</button></div><div id="rsvpUserList"></div></div>';
    div.innerHTML = html;
    if (roleId === 1 || roleId === 2) {
      loadRsvpUsers(id);
    }
  });
}

function toggleRsvp(id) {
  fetch(`/api/announcements/${id}/rsvp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })
  .then(r => r.json())
  .then(function() {
    loadRsvpSection(id, currentAnnouncementRoleId);
  });
}

function loadRsvpUsers(id) {
  fetch(`/api/announcements/${id}/rsvps`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })
  .then(r => {
    if (!r.ok) return null;
    return r.json();
  })
  .then(users => {
    if (!users || users.length === 0) return;
    var listDiv = document.getElementById('rsvpUserList');
    var html = '<div class="rsvp-user-list"><h5>Отметились:</h5>';
    users.forEach(function(u) {
      html += '<div class="rsvp-user-card"><span class="rsvp-user-name">' + u.user_name + '</span></div>';
    });
    html += '</div>';
    listDiv.innerHTML = html;
  });
}

function pluralize(n, one, few, many) {
  if (n % 10 === 1 && n % 100 !== 11) return one;
  if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) return few;
  return many;
}