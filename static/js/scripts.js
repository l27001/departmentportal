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