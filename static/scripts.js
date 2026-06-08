document.getElementById("selection-form").addEventListener("submit", function(event) {
    event.preventDefault();

    const studentId = document.getElementById("student-id").value;
    const studentId1 = document.getElementById("student-id1").value;
    const studentId2 = document.getElementById("student-id2").value;

    const selection = document.getElementById("selection").value;

    if (!studentId || !selection) {
        alert("请输入学号并选择一个选项！");
        return;
    }

    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: studentId,
            student_id1: studentId1,
            student_id2: studentId2,
            selection: selection
        })
    })
    .then(response => response.json())
    .then(data => {
        const messageElement = document.getElementById("message");
        
        // 根据返回的success字段更新页面
        if (data.success) {
            messageElement.style.color = 'green';
            messageElement.textContent = data.message;  // 显示成功消息
        } else {
            messageElement.style.color = 'red';
            messageElement.textContent = data.message;  // 显示失败消息
        }
    })
    .catch(error => {
        const messageElement = document.getElementById("message");
        messageElement.style.color = 'red';
        messageElement.textContent = "失败请稍后再试。";  // 网络错误提示
    });
});
document.getElementById("query-btn").addEventListener("click", function() {

    const studentId = document.getElementById("query-student-id").value;

    if (!studentId) {
        alert("请输入学号！");
        return;
    }

    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: studentId
        })
    })
    .then(response => response.json())
    .then(data => {

        const messageElement = document.getElementById("query-message");

        if (data.success) {
            messageElement.style.color = 'green';

            messageElement.innerHTML = `
                选择项目：${data.selection}<br>
                队友：${data.members.join(' , ')}
            `;
        }
        else {
            messageElement.style.color = 'red';
            messageElement.textContent = data.message;
        }
    })
    .catch(error => {

        const messageElement = document.getElementById("query-message");

        messageElement.style.color = 'red';
        messageElement.textContent = '未查到。';
    });
});
