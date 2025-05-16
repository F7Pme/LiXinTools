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

    // 设置默认排序为房间号
    window.currentSort = {
        field: 'room',
        direction: 'asc'
    };
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

    // 如果有设置默认排序，应用排序
    if (window.currentSort) {
        data = sortRoomData(data, window.currentSort.field, window.currentSort.direction);
    }

    data.forEach(item => {
        const row = document.createElement('tr');

        // 为低电量行添加警告样式
        if (item.electricity <= 0) {
            row.classList.add('table-danger');
        } else if (item.electricity <= 10) {
            row.classList.add('table-warning');
        }

        // 添加点击整行的样式和交互
        row.style.cursor = 'pointer';

        // 显示房间数据
        row.innerHTML = `
            <td>${item.building}</td>
            <td>${item.room}</td>
            <td>${Number(item.electricity).toFixed(2)}</td>
            <td>${getStatusBadge(item.electricity)}</td>
        `;

        // 为整行添加点击事件
        row.addEventListener('click', function () {
            showRoomHistory(item.building, item.room);
        });

        tableBody.appendChild(row);
    });

    // 更新表头排序图标
    updateSortHeaderStyles();
}

/**
 * 获取状态徽章
 */
function getStatusBadge(electricity) {
    if (electricity <= 0) {
        return '<span class="badge bg-danger">紧急</span>';
    } else if (electricity <= 10) {
        return '<span class="badge bg-warning text-dark">警告</span>';
    } else {
        return '<span class="badge bg-success">正常</span>';
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
    const criticalCount = data.filter(item => item.electricity <= 0).length;
    const warningCount = data.filter(item => item.electricity > 0 && item.electricity <= 10).length;
    const normalCount = data.filter(item => item.electricity > 10).length;

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
            <span class="text-danger">紧急 (${criticalCount})</span>
            <span class="text-warning">警告 (${warningCount})</span>
            <span class="text-success">正常 (${normalCount})</span>
        </div>
        <div class="progress mb-3" style="height: 24px; border-radius: 12px; overflow: hidden;">
            <div class="progress-bar bg-danger" style="width: ${(criticalCount / totalRooms * 100)}%" title="紧急: ${criticalCount}间">${criticalCount > 0 ? criticalCount : ''}</div>
            <div class="progress-bar bg-warning" style="width: ${(warningCount / totalRooms * 100)}%" title="警告: ${warningCount}间">${warningCount > 0 ? warningCount : ''}</div>
            <div class="progress-bar bg-success" style="width: ${(normalCount / totalRooms * 100)}%" title="正常: ${normalCount}间">${normalCount > 0 ? normalCount : ''}</div>
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

            // 计算所有楼栋的总电量用于比较
            let totalElectricityAll = 0;
            let maxTotalElectricity = 0;

            data.building_stats.forEach(building => {
                // 计算该楼栋的总电量 (平均电量 × 房间数)
                const buildingTotalElectricity = building.average * building.count;
                totalElectricityAll += buildingTotalElectricity;

                // 记录最大的楼栋总电量，用于进度条比例
                if (buildingTotalElectricity > maxTotalElectricity) {
                    maxTotalElectricity = buildingTotalElectricity;
                }

                // 将总电量添加到对象中
                building.totalElectricity = buildingTotalElectricity;
            });

            // 根据总电量排序（从高到低）
            data.building_stats.sort((a, b) => b.totalElectricity - a.totalElectricity);

            const buildingCards = data.building_stats.map(building => {
                // 计算该楼栋电量占所有楼栋最大电量的百分比，用于进度条
                const electricityPercentage = (building.totalElectricity / maxTotalElectricity * 100);

                // 计算进度条颜色 - 基于平均电量
                let progressClass = "bg-success";
                if (building.average <= 0) {
                    progressClass = "bg-danger";
                } else if (building.average <= 10) {
                    progressClass = "bg-warning";
                }

                return `
                    <div class="card mb-2">
                        <div class="card-body p-2">
                            <div class="d-flex justify-content-between">
                                <h6 class="card-title mb-1">${building.building}栋</h6>
                                <span class="badge bg-primary">${building.count}间</span>
                            </div>
                            <div class="d-flex justify-content-between mt-1 small text-muted">
                                <span>总电量: ${building.totalElectricity.toFixed(1)}度</span>
                                <span>平均: ${building.average.toFixed(1)}度</span>
                            </div>
                            <div class="progress mt-2" style="height: 8px; border-radius: 4px;">
                                <div class="progress-bar ${progressClass}" style="width: ${electricityPercentage}%" 
                                     title="总电量: ${building.totalElectricity.toFixed(1)}度"></div>
                            </div>
                            <div class="d-flex justify-content-between mt-1 small text-muted">
                                <span>最低: ${building.min.toFixed(1)}</span>
                                <span>最高: ${building.max.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

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
    // 获取当前排序方向
    const header = document.querySelector(`.sortable[data-field="${field}"]`);
    const currentDirection = header.getAttribute('data-direction') || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

    // 存储当前排序状态
    window.currentSort = {
        field: field,
        direction: newDirection
    };

    // 重置所有表头的排序状态
    document.querySelectorAll('.sortable').forEach(h => {
        h.setAttribute('data-direction', '');
        h.querySelector('i').className = 'bi bi-arrow-down-up';
    });

    // 设置当前表头的排序状态
    header.setAttribute('data-direction', newDirection);
    header.querySelector('i').className = newDirection === 'asc' ? 'bi bi-arrow-down' : 'bi bi-arrow-up';

    // 获取数据并排序
    const tableBody = document.getElementById('room-data');
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    // 处理没有数据的情况
    if (rows.length <= 1 && rows[0]?.cells?.length !== 4) {
        return;
    }

    // 从行中提取数据
    const data = [];
    rows.forEach(row => {
        if (row.cells.length === 4) {
            data.push({
                building: row.cells[0].textContent,
                room: row.cells[1].textContent,
                electricity: parseFloat(row.cells[2].textContent),
                status: row.cells[3].textContent
            });
        }
    });

    // 排序数据
    const sortedData = sortRoomData(data, field, newDirection);

    // 重新显示排序后的数据
    displayElectricityData(sortedData);
}

/**
 * 排序房间数据
 */
function sortRoomData(data, field, direction) {
    return [...data].sort((a, b) => {
        let result = 0;

        switch (field) {
            case 'building':
                // 按楼栋排序 - 直接比较数字
                result = parseInt(a.building) - parseInt(b.building);
                break;

            case 'room':
                // 按房间号排序 - 特殊处理逻辑
                const roomA = parseRoomNumber(a.room);
                const roomB = parseRoomNumber(b.room);
                result = compareRoomNumbers(roomA, roomB);
                break;

            case 'electricity':
                // 按电量排序
                result = a.electricity - b.electricity;
                break;

            case 'status':
                // 按状态排序 - 根据电量判断状态优先级
                const priorityA = getStatusPriority(a.electricity);
                const priorityB = getStatusPriority(b.electricity);
                result = priorityA - priorityB;
                break;

            default:
                // 默认不排序
                return 0;
        }

        // 应用排序方向
        return direction === 'asc' ? result : -result;
    });
}

/**
 * 解析房间号
 */
function parseRoomNumber(roomStr) {
    // 处理形式为 "1-1001" 的房间号，其中1是楼栋，1001表示10楼01房间
    const parts = roomStr.split('-');

    if (parts.length > 1) {
        const roomNumber = parts[1];
        // 对于4位数的房间号，第1-2位是楼层，后2位是房间号
        if (roomNumber.length === 4) {
            return {
                floor: parseInt(roomNumber.substring(0, 2)),
                room: parseInt(roomNumber.substring(2))
            };
        }
    }

    // 如果不是标准格式，尝试提取数字部分
    const matches = roomStr.match(/(\d+)/g);
    if (matches && matches.length > 0) {
        const roomNum = parseInt(matches[matches.length - 1]);
        if (roomNum > 100) {
            return {
                floor: Math.floor(roomNum / 100),
                room: roomNum % 100
            };
        }
        return { floor: 0, room: roomNum };
    }

    // 无法解析时返回默认值
    return { floor: 0, room: 0 };
}

/**
 * 比较两个房间号
 */
function compareRoomNumbers(roomA, roomB) {
    // 首先比较楼层
    if (roomA.floor !== roomB.floor) {
        return roomA.floor - roomB.floor;
    }

    // 楼层相同则比较房间号
    return roomA.room - roomB.room;
}

/**
 * 获取状态优先级
 */
function getStatusPriority(electricity) {
    if (electricity <= 0) return 1; // 紧急 - 最高优先级
    if (electricity <= 10) return 2; // 警告
    return 3; // 正常
}

/**
 * 更新表头排序样式
 */
function updateSortHeaderStyles() {
    if (!window.currentSort) return;

    const headers = document.querySelectorAll('.sortable');

    headers.forEach(header => {
        const field = header.getAttribute('data-field');

        // 重置所有表头样式
        header.setAttribute('data-direction', '');
        header.querySelector('i').className = 'bi bi-arrow-down-up';

        // 设置当前排序表头的样式
        if (field === window.currentSort.field) {
            header.setAttribute('data-direction', window.currentSort.direction);
            header.querySelector('i').className =
                window.currentSort.direction === 'asc' ? 'bi bi-arrow-down' : 'bi bi-arrow-up';
        }
    });
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