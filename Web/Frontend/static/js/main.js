/**
 * 电量查询系统前端JavaScript
 * 版本: v1.0.5
 */

document.addEventListener('DOMContentLoaded', function () {
    // 初始化
    initialize();
});

/**
 * 初始化函数
 */
function initialize() {
    // 加载最新查询时间
    fetchLatestQueryTime();

    // 加载电量数据
    fetchElectricityData();

    // 加载分析结果
    fetchAnalysisResult();

    // 加载查询历史
    fetchQueryHistory();

    // 加载楼栋统计
    fetchBuildingStats();

    // 加载历史时间点
    fetchHistoryTimes();

    // 添加事件监听器
    attachEventListeners();
}

/**
 * 添加事件监听器
 */
function attachEventListeners() {
    // 绑定搜索按钮
    document.getElementById('search-button').addEventListener('click', searchRooms);

    // 绑定搜索输入框回车事件
    document.getElementById('room-search').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            searchRooms();
        }
    });

    // 绑定排序表头
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const field = this.getAttribute('data-field');
            sortTable(field);
        });
    });

    // 绑定历史选择器
    document.getElementById('history-selector').addEventListener('change', function () {
        const selectedValue = this.value;
        if (selectedValue === 'latest') {
            fetchElectricityData();
        } else {
            fetchHistoryData(selectedValue);
        }
    });

    // 绑定修复数据按钮
    document.getElementById('fix-data-btn').addEventListener('click', fixHistoryData);
}

/**
 * 获取最新查询时间
 */
function fetchLatestQueryTime() {
    fetch('/api/latest_query_time')
        .then(response => response.json())
        .then(data => {
            document.getElementById('latest-query-time').textContent = '最新查询时间: ' + data.query_time;
        })
        .catch(error => {
            console.error('获取最新查询时间出错:', error);
            document.getElementById('latest-query-time').textContent = '最新查询时间: 获取失败';
        });
}

/**
 * 获取电量数据
 */
function fetchElectricityData() {
    // 显示加载状态
    document.getElementById('room-data').innerHTML = `
        <tr>
            <td colspan="4" class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-3">正在加载房间数据...</p>
            </td>
        </tr>
    `;

    fetch('/api/electricity_data')
        .then(response => response.json())
        .then(data => {
            displayElectricityData(data.data);
            updateOverallStats(data.data);

            // 更新最新查询时间
            document.getElementById('latest-query-time').textContent = '最新查询时间: ' + data.query_time;

            // 更新历史选择器显示
            const historySelector = document.getElementById('history-selector');
            if (historySelector.options[0].value === 'latest') {
                historySelector.options[0].text = `最新数据 (${data.query_time})`;
            }
        })
        .catch(error => {
            console.error('获取电量数据出错:', error);
            document.getElementById('room-data').innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5 text-danger">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <p>获取数据失败，请稍后再试</p>
                    </td>
                </tr>
            `;
        });
}

/**
 * 显示电量数据
 */
function displayElectricityData(data) {
    const tableBody = document.getElementById('room-data');
    tableBody.innerHTML = '';

    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-info-circle"></i>
                    <p>暂无电量数据</p>
                </td>
            </tr>
        `;
        return;
    }

    data.forEach(item => {
        const row = document.createElement('tr');

        // 为低电量行添加警告样式
        if (item.electricity < 10) {
            row.classList.add('table-danger');
        } else if (item.electricity < 30) {
            row.classList.add('table-warning');
        }

        // 在房间单元格添加点击事件
        row.innerHTML = `
            <td>${item.building}</td>
            <td><a href="#" class="room-link" data-building="${item.building}" data-room="${item.room}">${item.room}</a></td>
            <td>${Number(item.electricity).toFixed(2)}</td>
            <td>${getStatusBadge(item.electricity)}</td>
        `;

        tableBody.appendChild(row);
    });

    // 为房间链接添加点击事件
    document.querySelectorAll('.room-link').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const building = this.getAttribute('data-building');
            const room = this.getAttribute('data-room');
            showRoomHistory(building, room);
        });
    });
}

/**
 * 获取状态徽章
 */
function getStatusBadge(electricity) {
    if (electricity < 10) {
        return '<span class="badge bg-danger">紧急</span>';
    } else if (electricity < 30) {
        return '<span class="badge bg-warning text-dark">警告</span>';
    } else if (electricity < 60) {
        return '<span class="badge bg-info text-dark">正常</span>';
    } else {
        return '<span class="badge bg-success">充足</span>';
    }
}

/**
 * 更新总体统计
 */
function updateOverallStats(data) {
    if (!data || data.length === 0) {
        document.getElementById('overall-stats').innerHTML = `
            <div class="alert alert-info mb-0">
                <i class="bi bi-info-circle"></i> 暂无统计数据
                    </div>
                `;
        return;
    }

    // 计算总体统计数据
    const totalRooms = data.length;
    const electricityValues = data.map(item => parseFloat(item.electricity));
    const totalElectricity = electricityValues.reduce((sum, current) => sum + current, 0);
    const avgElectricity = totalElectricity / totalRooms;
    const minElectricity = Math.min(...electricityValues);
    const maxElectricity = Math.max(...electricityValues);

    // 计算不同状态的房间数量
    const criticalCount = data.filter(item => item.electricity < 10).length;
    const warningCount = data.filter(item => item.electricity >= 10 && item.electricity < 30).length;
    const normalCount = data.filter(item => item.electricity >= 30 && item.electricity < 60).length;
    const goodCount = data.filter(item => item.electricity >= 60).length;

    document.getElementById('overall-stats').innerHTML = `
        <div class="row mb-2">
                    <div class="col-6">
                <div class="text-muted small">总房间数</div>
                <div class="fs-5">${totalRooms}</div>
                    </div>
                    <div class="col-6">
                <div class="text-muted small">平均电量</div>
                <div class="fs-5">${avgElectricity.toFixed(2)} 度</div>
                        </div>
                    </div>
        <div class="row mb-3">
                    <div class="col-6">
                <div class="text-muted small">最低电量</div>
                <div class="fs-5">${minElectricity.toFixed(2)} 度</div>
                    </div>
                    <div class="col-6">
                <div class="text-muted small">最高电量</div>
                <div class="fs-5">${maxElectricity.toFixed(2)} 度</div>
                        </div>
                    </div>
        
        <div class="text-muted small mb-2">电量状态分布</div>
        <div class="d-flex justify-content-between mb-1 small">
            <span>紧急 (${criticalCount})</span>
            <span>警告 (${warningCount})</span>
            <span>正常 (${normalCount})</span>
            <span>充足 (${goodCount})</span>
                </div>
        <div class="progress" style="height: 20px;">
            <div class="progress-bar bg-danger" style="width: ${(criticalCount / totalRooms * 100)}%">${criticalCount}</div>
            <div class="progress-bar bg-warning" style="width: ${(warningCount / totalRooms * 100)}%">${warningCount}</div>
            <div class="progress-bar bg-info" style="width: ${(normalCount / totalRooms * 100)}%">${normalCount}</div>
            <div class="progress-bar bg-success" style="width: ${(goodCount / totalRooms * 100)}%">${goodCount}</div>
                </div>
            `;
}

/**
 * 获取分析结果
 */
function fetchAnalysisResult() {
    document.getElementById('analysis-result').innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
                </div>
            <p>正在加载分析结果...</p>
            </div>
        `;

    fetch('/api/analysis')
        .then(response => response.json())
        .then(data => {
            if (!data.analysis_lines || data.analysis_lines.length === 0) {
                document.getElementById('analysis-result').innerHTML = `
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle"></i> 暂无分析数据
                    </div>
                `;
                return;
            }

            const analysisHtml = data.analysis_lines.map(line => {
                // 处理重点信息的样式
                if (line.includes('紧急') || line.includes('不足') || line.includes('警告')) {
                    return `<div class="text-danger">${line}</div>`;
                } else if (line.includes('最高') || line.includes('最低')) {
                    return `<div class="text-primary">${line}</div>`;
                } else if (line.includes('平均') || line.includes('总体')) {
                    return `<div class="text-success">${line}</div>`;
                } else {
                    return `<div>${line}</div>`;
                }
            }).join('');

            document.getElementById('analysis-result').innerHTML = analysisHtml;
        })
        .catch(error => {
            console.error('获取分析结果出错:', error);
            document.getElementById('analysis-result').innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle-fill"></i> 获取分析结果失败
                </div>
            `;
        });
}

/**
 * 获取查询历史
 */
function fetchQueryHistory() {
    document.getElementById('query-history').innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p>正在加载查询历史...</p>
        </div>
    `;

    fetch('/api/query_history')
        .then(response => response.json())
        .then(data => {
            if (!data.history || data.history.length === 0) {
                document.getElementById('query-history').innerHTML = `
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle"></i> 暂无查询历史
                    </div>
                `;
                return;
            }

            const historyList = data.history.map(item => `
                <li class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="ms-2 me-auto">
                        <div class="fw-bold small">${item.description || '查询记录'}</div>
                        <small class="text-muted">${item.query_time}</small>
                    </div>
                    <span class="badge bg-primary rounded-pill">#${item.id}</span>
                </li>
            `).join('');

            document.getElementById('query-history').innerHTML = `
                <ol class="list-group list-group-flush list-group-numbered">
                    ${historyList}
                </ol>
            `;
        })
        .catch(error => {
            console.error('获取查询历史出错:', error);
            document.getElementById('query-history').innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle-fill"></i> 获取查询历史失败
                </div>
            `;
        });
}

/**
 * 获取楼栋统计数据
 */
function fetchBuildingStats() {
    document.getElementById('building-stats').innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p>正在加载楼栋数据...</p>
        </div>
    `;

    fetch('/api/building_data')
        .then(response => response.json())
        .then(data => {
            if (!data.building_stats || data.building_stats.length === 0) {
                document.getElementById('building-stats').innerHTML = `
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle"></i> 暂无楼栋统计数据
                    </div>
                `;
                return;
            }

            const buildingCards = data.building_stats.map(building => `
                <div class="card mb-2">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between">
                            <h6 class="card-title mb-1">${building.building}栋</h6>
                            <span class="badge bg-primary">${building.count}间</span>
                        </div>
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar" style="width: ${Math.min(100, building.average / building.max * 100)}%"></div>
                        </div>
                        <div class="d-flex justify-content-between mt-1 small text-muted">
                            <span>最低: ${building.min.toFixed(1)}</span>
                            <span>平均: ${building.average.toFixed(1)}</span>
                            <span>最高: ${building.max.toFixed(1)}</span>
                        </div>
                    </div>
                </div>
            `).join('');

            document.getElementById('building-stats').innerHTML = buildingCards;
        })
        .catch(error => {
            console.error('获取楼栋统计出错:', error);
            document.getElementById('building-stats').innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle-fill"></i> 获取楼栋统计失败
                </div>
            `;
        });
}

/**
 * 获取历史时间点
 */
function fetchHistoryTimes() {
    fetch('/api/history_times')
        .then(response => response.json())
        .then(data => {
            if (!data.history_times || data.history_times.length === 0) {
                return;
            }

            const historySelector = document.getElementById('history-selector');

            // 清除除了"latest"选项外的所有选项
            while (historySelector.options.length > 1) {
                historySelector.remove(1);
            }

            // 添加新的时间点选项
            data.history_times.forEach(time => {
                const option = document.createElement('option');
                option.value = time.time_id;
                option.text = time.description + ' (' + time.query_time + ')';
                historySelector.appendChild(option);
            });
        })
        .catch(error => {
            console.error('获取历史时间点出错:', error);
        });
}

/**
 * 获取历史数据
 */
function fetchHistoryData(timeId) {
    // 显示加载状态
    document.getElementById('room-data').innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="mt-3">正在加载历史数据...</p>
                    </td>
                </tr>
            `;

    fetch(`/api/history_data/${timeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('room-data').innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5 text-danger">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <p>${data.error}</p>
                        </td>
                    </tr>
                `;
                return;
            }

            document.getElementById('latest-query-time').textContent = '查询时间: ' + data.query_time;
            displayElectricityData(data.data || data.electricity_data);
            updateOverallStats(data.data || data.electricity_data);
        })
        .catch(error => {
            console.error('获取历史数据出错:', error);
            document.getElementById('room-data').innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5 text-danger">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <p>获取历史数据失败</p>
                        </td>
                    </tr>
                `;
        });
}

/**
 * 搜索房间
 */
function searchRooms() {
    const searchInput = document.getElementById('room-search').value.trim().toLowerCase();

    if (!searchInput) {
        // 如果搜索框为空，重新加载所有数据
        const historySelector = document.getElementById('history-selector');
        const selectedValue = historySelector.value;

        if (selectedValue === 'latest') {
            fetchElectricityData();
        } else {
            fetchHistoryData(selectedValue);
        }
        return;
    }

    const rows = document.getElementById('room-data').querySelectorAll('tr');
    let foundAny = false;

    rows.forEach(row => {
        const building = row.cells[0]?.textContent.toLowerCase() || '';
        const room = row.cells[1]?.textContent.toLowerCase() || '';

        if (building.includes(searchInput) || room.includes(searchInput)) {
            row.style.display = '';
            foundAny = true;
        } else {
            row.style.display = 'none';
        }
    });

    // 如果没有找到任何匹配的房间，显示提示
    if (!foundAny) {
        document.getElementById('room-data').innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-search"></i>
                    <p>未找到符合条件的房间: "${searchInput}"</p>
                </td>
            </tr>
        `;
    }
}

/**
 * 排序表格
 */
function sortTable(field) {
    const tbody = document.getElementById('room-data');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // 如果没有有效行，直接返回
    if (rows.length <= 1) {
        return;
    }

    // 查找当前排序状态
    const header = document.querySelector(`.sortable[data-field="${field}"]`);
    const currentDirection = header.getAttribute('data-direction') || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

    // 重置所有表头的排序状态
    document.querySelectorAll('.sortable').forEach(h => {
        h.setAttribute('data-direction', '');
        h.querySelector('i').className = 'bi bi-arrow-down-up';
    });

    // 设置当前表头的排序状态
    header.setAttribute('data-direction', newDirection);
    header.querySelector('i').className = newDirection === 'asc' ? 'bi bi-arrow-down' : 'bi bi-arrow-up';

    // 排序行
    rows.sort((a, b) => {
        // 确保是有效的行
        if (!a.cells || !b.cells) {
            return 0;
        }

        let valueA, valueB;

        switch (field) {
            case 'building':
                valueA = a.cells[0].textContent;
                valueB = b.cells[0].textContent;
                break;
            case 'room':
                valueA = a.cells[1].textContent;
                valueB = b.cells[1].textContent;
                break;
            case 'electricity':
                valueA = parseFloat(a.cells[2].textContent);
                valueB = parseFloat(b.cells[2].textContent);
                break;
            case 'status':
                valueA = a.cells[3].textContent;
                valueB = b.cells[3].textContent;
                break;
            default:
                return 0;
        }

        if (field === 'electricity') {
            return newDirection === 'asc' ? valueA - valueB : valueB - valueA;
        } else {
            const comparison = valueA.localeCompare(valueB);
            return newDirection === 'asc' ? comparison : -comparison;
        }
    });

    // 重新添加排序后的行
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * 显示房间历史数据
 */
function showRoomHistory(building, room) {
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('roomHistoryModal'));
    modal.show();

    // 显示加载状态
    document.getElementById('room-history-loading').style.display = 'block';
    document.getElementById('room-history-content').style.display = 'none';
    document.getElementById('room-history-error').style.display = 'none';

    // 设置标题
    document.getElementById('room-history-title').textContent = `${building}栋 - ${room}`;

    // 获取数据
    fetch(`/api/room_history/${building}/${room}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('room-history-loading').style.display = 'none';
                document.getElementById('room-history-error').style.display = 'block';
                document.getElementById('room-history-error').textContent = data.error;
                return;
            }

            document.getElementById('room-history-loading').style.display = 'none';
            document.getElementById('room-history-content').style.display = 'block';

            // 如果没有历史数据
            if (!data.history || data.history.length === 0) {
                document.getElementById('room-history-data').innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center py-3">
                            <i class="bi bi-info-circle"></i> 暂无历史数据
                        </td>
                    </tr>
                `;

                // 隐藏图表
                document.querySelector('.chart-container').style.display = 'none';
                return;
            }

            // 显示图表
            document.querySelector('.chart-container').style.display = 'block';

            // 处理数据，按时间排序
            const sortedHistory = [...data.history].sort((a, b) => {
                return new Date(a.query_time) - new Date(b.query_time);
            });

            // 计算消耗电量
            for (let i = 1; i < sortedHistory.length; i++) {
                const prev = sortedHistory[i - 1].electricity;
                const curr = sortedHistory[i].electricity;

                // 如果当前电量比前一次高，可能是充值了
                sortedHistory[i].consumed = prev > curr ? (prev - curr).toFixed(2) : '0.00';
            }
            sortedHistory[0].consumed = '0.00';  // 第一条记录没有消耗

            // 显示表格数据
            const tableHtml = sortedHistory.reverse().map(record => `
                <tr>
                    <td>${record.query_time}</td>
                    <td>${record.electricity.toFixed(2)}</td>
                    <td>${record.consumed}</td>
                </tr>
            `).join('');

            document.getElementById('room-history-data').innerHTML = tableHtml;

            // 显示图表
            createElectricityChart(sortedHistory.reverse());  // 图表需要按时间正序排列
        })
        .catch(error => {
            console.error('获取房间历史数据出错:', error);
            document.getElementById('room-history-loading').style.display = 'none';
            document.getElementById('room-history-error').style.display = 'block';
            document.getElementById('room-history-error').textContent = '获取数据时出错: ' + error.message;
        });
}

/**
 * 创建电量图表
 */
function createElectricityChart(history) {
    const ctx = document.getElementById('electricityChart').getContext('2d');

    // 如果有旧图表，销毁它（添加更严格的类型检查）
    if (window.electricityChart && typeof window.electricityChart === 'object' && typeof window.electricityChart.destroy === 'function') {
        try {
            window.electricityChart.destroy();
        } catch (error) {
            console.error('销毁旧图表时出错:', error);
            // 忽略错误，继续创建新图表
        }
    }

    // 如果还有问题，尝试清空canvas并重新创建
    const canvas = document.getElementById('electricityChart');
    if (canvas) {
        // 清空当前canvas
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    }

    // 确保Chart.js库已加载
    if (typeof Chart === 'undefined') {
        console.error('Chart.js库未加载');
        return;
    }

    try {
        // 准备数据
        const labels = history.map(item => {
            // 简化时间显示，只显示MM-DD HH:MM
            const date = new Date(item.query_time.replace(/-/g, '/'));
            return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        });

        const data = history.map(item => item.electricity);

        // 创建图表
        window.electricityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '剩余电量(度)',
                    data: data,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const record = history[index];
                                return [
                                    `电量: ${record.electricity.toFixed(2)}度`,
                                    `时间: ${record.query_time}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '电量(度)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '时间'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('创建图表时出错:', error);
    }
}

/**
 * 修复历史数据
 */
function fixHistoryData() {
    const fixButton = document.getElementById('fix-data-btn');
    const originalText = fixButton.textContent;

    // 禁用按钮并显示加载状态
    fixButton.disabled = true;
    fixButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 修复中...';

    fetch('/api/fix_history_data', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            fixButton.disabled = false;
            fixButton.textContent = originalText;

            // 显示结果
            const diagnosisInfo = document.getElementById('diagnosis-info');
            if (data.success) {
                diagnosisInfo.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle-fill"></i> ${data.message}
                    </div>
                `;
            } else {
                diagnosisInfo.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill"></i> ${data.message}
                        ${data.errors && data.errors.length > 0 ?
                        `<ul class="mt-2 mb-0">
                                ${data.errors.map(err => `<li>${err}</li>`).join('')}
                            </ul>` :
                        ''}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('修复数据出错:', error);

            // 恢复按钮状态
            fixButton.disabled = false;
            fixButton.textContent = originalText;

            // 显示错误信息
            document.getElementById('diagnosis-info').innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i> 修复数据时发生错误: ${error.message}
                </div>
            `;
        });
} 