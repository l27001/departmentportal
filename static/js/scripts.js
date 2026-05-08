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

function updateTaskStatus(el, id) {
    var taskItem = el.closest('.task-item');
    var newVal = el.value;
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
        var modal = document.getElementById('taskDetailsModal');
        if (modal && modal.style.display === 'block') {
            openTaskDetails(id);
        }
    })
}