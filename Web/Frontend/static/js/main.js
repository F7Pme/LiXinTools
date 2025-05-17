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
        if (item.electricity <= 0) {
            row.classList.add('table-danger');
        } else if (item.electricity <= 10) {
            row.classList.add('table-warning');
        }
        row.style.cursor = 'pointer';
        // 只在building为纯数字时添加“新苑x号楼”，否则直接显示原building
        let buildingName = item.building;
        if (/^\d+$/.test(item.building)) {
            buildingName = `新苑${item.building}号楼`;
        }
        row.innerHTML = `
            <td>${buildingName}</td>
            <td>${item.room}</td>
            <td>${Number(item.electricity).toFixed(2)}</td>
            <td>${getStatusBadge(item.electricity)}</td>
        `;
        row.addEventListener('click', function () {
            showRoomHistory(item.building, item.room);
        });
        tableBody.appendChild(row);
    });
    updateSortHeaderStyles();
}

/**
 * 获取状态徽章
 */
function getStatusBadge(electricity) {
    if (electricity <= 0) {
        return '<span class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill me-1"></i>紧急</span>';
    } else if (electricity <= 10) {
        return '<span class="badge bg-warning"><i class="bi bi-exclamation-fill me-1"></i>警告</span>';
    } else {
        return '<span class="badge bg-success"><i class="bi bi-check-circle-fill me-1"></i>正常</span>';
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

    const totalRooms = data.length;
    const electricityValues = data.map(item => parseFloat(item.electricity));
    const totalElectricity = electricityValues.reduce((sum, current) => sum + current, 0);
    const avgElectricity = totalElectricity / totalRooms;
    const minElectricity = Math.min(...electricityValues);
    const maxElectricity = Math.max(...electricityValues);

    const criticalCount = data.filter(item => item.electricity <= 0).length;
    const warningCount = data.filter(item => item.electricity > 0 && item.electricity <= 10).length;
    const normalCount = data.filter(item => item.electricity > 10).length;

    const criticalPercent = (criticalCount / totalRooms * 100).toFixed(1);
    const warningPercent = (warningCount / totalRooms * 100).toFixed(1);
    const normalPercent = (normalCount / totalRooms * 100).toFixed(1);

    // 最小宽度逻辑
    const minDisplayWidth = 3;
    let criticalWidth = parseFloat(criticalPercent);
    let warningWidth = parseFloat(warningPercent);
    let normalWidth = parseFloat(normalPercent);
    if (criticalCount > 0 && criticalWidth < minDisplayWidth) {
        criticalWidth = minDisplayWidth;
        if (normalWidth > criticalWidth * 2) {
            normalWidth -= (minDisplayWidth - parseFloat(criticalPercent));
        } else if (warningWidth > criticalWidth * 2) {
            warningWidth -= (minDisplayWidth - parseFloat(criticalPercent));
        }
    }
    if (warningCount > 0 && warningWidth < minDisplayWidth) {
        warningWidth = minDisplayWidth;
        if (normalWidth > warningWidth * 2) {
            normalWidth -= (minDisplayWidth - parseFloat(warningPercent));
        }
    }

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
        <div class="progress my-4">
            <div class="progress-bar bg-success" style="width: ${normalWidth}%" 
                title="正常: ${normalCount}间 (${normalPercent}%)">
                ${normalCount} (${normalPercent}%)
            </div>
            <div class="progress-bar bg-warning" style="width: ${warningWidth}%" 
                title="警告: ${warningCount}间">
                ${warningCount}
            </div>
            <div class="progress-bar bg-danger" style="width: ${criticalWidth}%" 
                title="紧急: ${criticalCount}间">
                ${criticalCount}
            </div>
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
                let iconClass = "bi-lightning-charge-fill";

                if (building.average <= 0) {
                    progressClass = "bg-danger";
                    iconClass = "bi-exclamation-triangle-fill";
                } else if (building.average <= 10) {
                    progressClass = "bg-warning";
                    iconClass = "bi-exclamation-fill";
                }

                // 格式化楼栋名称
                const buildingName = `新苑${building.building}号楼`;

                return `
                    <div class="building-card">
                        <div class="building-header">
                            <span class="building-title">
                                <i class="bi bi-building"></i> ${buildingName}
                            </span>
                            <span class="building-count">${building.count}间</span>
                        </div>
                        <div class="building-stats-row">
                            <div>
                                <div class="stat-label">总电量</div>
                                <div class="stat-value">${building.totalElectricity.toFixed(1)}</div>
                            </div>
                            <div>
                                <div class="stat-label">平均</div>
                                <div class="stat-value">${building.average.toFixed(1)}</div>
                            </div>
                            <div>
                                <div class="stat-label">
                                    <i class="bi ${iconClass} ${progressClass === 'bg-danger' ? 'text-danger' : (progressClass === 'bg-warning' ? 'text-warning' : 'text-success')}"></i>
                                </div>
                                <div class="stat-value">${building.min.toFixed(1)}~${building.max.toFixed(1)}</div>
                            </div>
                        </div>
                        <div class="building-progress">
                            <div class="progress-bar ${progressClass}" style="width:${electricityPercentage}%"></div>
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

                // 首先比较了楼栋
                if (a.building !== b.building) {
                    result = parseInt(a.building) - parseInt(b.building);
                } else {
                    // 楼栋相同，使用compareRoomNumbers比较
                    result = compareRoomNumbers(roomA, roomB);
                }
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
    // 处理形式为 "4-1312" 的房间号，其中4是楼栋，13表示13楼，12表示房间号
    const parts = roomStr.split('-');

    if (parts.length > 1) {
        const building = parseInt(parts[0]);
        const roomNumber = parts[1];

        // 对于3位或4位数的房间号
        if (roomNumber.length >= 3) {
            // 最后两位是房间号
            const room = parseInt(roomNumber.substring(roomNumber.length - 2));
            // 前面的部分是楼层
            const floor = parseInt(roomNumber.substring(0, roomNumber.length - 2));

            return {
                building: building,
                floor: floor,
                room: room
            };
        } else {
            // 对于小于3位的房间号，可能是简化表示，如1-01
            return {
                building: building,
                floor: 0,
                room: parseInt(roomNumber)
            };
        }
    }

    // 如果不是标准格式，尝试提取数字部分
    const matches = roomStr.match(/(\d+)/g);
    if (matches && matches.length > 0) {
        return {
            building: 0,
            floor: 0,
            room: parseInt(matches[matches.length - 1])
        };
    }

    // 无法解析时返回默认值
    return {
        building: 0,
        floor: 0,
        room: 0
    };
}

/**
 * 比较两个房间号
 */
function compareRoomNumbers(roomA, roomB) {
    // 首先比较楼栋
    if (roomA.building !== roomB.building) {
        return roomA.building - roomB.building;
    }

    // 楼栋相同则比较楼层
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
    const modal = new bootstrap.Modal(document.getElementById('roomHistoryModal'));
    modal.show();
    document.getElementById('room-history-loading').style.display = 'block';
    document.getElementById('room-history-content').style.display = 'none';
    document.getElementById('room-history-error').style.display = 'none';
    // 楼栋名格式
    const buildingName = `新苑${building}号楼`;
    document.getElementById('room-history-title').textContent = `${buildingName} - ${room}`;
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
            if (!data.history || data.history.length === 0) {
                document.getElementById('room-history-data').innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center py-3">
                            <i class="bi bi-info-circle"></i> 暂无历史数据
                        </td>
                    </tr>
                `;
                document.querySelector('.chart-container').style.display = 'none';
                return;
            }
            document.querySelector('.chart-container').style.display = 'block';
            const sortedHistory = [...data.history].sort((a, b) => {
                return new Date(a.query_time) - new Date(b.query_time);
            });
            for (let i = 1; i < sortedHistory.length; i++) {
                const prev = sortedHistory[i - 1].electricity;
                const curr = sortedHistory[i].electricity;
                const diff = prev - curr;
                sortedHistory[i].consumed = Math.max(0, diff).toFixed(2);
                sortedHistory[i].change = diff > 0 ? 'decrease' : (diff < 0 ? 'increase' : 'same');
            }
            sortedHistory[0].consumed = '0.00';
            sortedHistory[0].change = 'same';
            // 表格数据，时间格式YYYY-MM-DD HH:mm:ss
            const tableHtml = sortedHistory.reverse().map(record => {
                let changeIcon = '';
                let changeStyle = '';
                if (record.change === 'decrease') {
                    changeIcon = '<i class="bi bi-arrow-down-short text-danger"></i>';
                    changeStyle = 'text-danger';
                } else if (record.change === 'increase') {
                    changeIcon = '<i class="bi bi-arrow-up-short text-success"></i>';
                    changeStyle = 'text-success';
                }
                const formattedTime = formatQueryTimeFull(record.query_time);
                return `
                    <tr>
                        <td>${formattedTime}</td>
                        <td>${record.electricity.toFixed(2)}</td>
                        <td class="${changeStyle}">${changeIcon} ${record.consumed}</td>
                    </tr>
                `;
            }).join('');
            document.getElementById('room-history-data').innerHTML = tableHtml;
            createElectricityChart(sortedHistory.reverse(), buildingName, room);
        })
        .catch(error => {
            console.error('获取房间历史数据出错:', error);
            document.getElementById('room-history-loading').style.display = 'none';
            document.getElementById('room-history-error').style.display = 'block';
            document.getElementById('room-history-error').textContent = '获取数据时出错: ' + error.message;
        });
}

function formatQueryTimeFull(timeString) {
    const date = new Date(timeString.replace(/-/g, '/'));
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    const second = date.getSeconds().toString().padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function createElectricityChart(history, buildingName, room) {
    const ctx = document.getElementById('electricityChart').getContext('2d');
    if (window.electricityChart && typeof window.electricityChart === 'object' && typeof window.electricityChart.destroy === 'function') {
        try {
            window.electricityChart.destroy();
        } catch (error) {
            console.error('销毁旧图表时出错:', error);
        }
    }
    const canvas = document.getElementById('electricityChart');
    if (canvas) {
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    }
    if (typeof Chart === 'undefined') {
        console.error('Chart.js库未加载');
        return;
    }
    try {
        const labels = history.map(item => formatQueryTimeFull(item.query_time));
        const data = history.map(item => item.electricity);
        let minValue = Math.min(...data) * 0.9;
        minValue = Math.max(0, minValue);
        const maxValue = Math.max(...data) * 1.1;
        window.electricityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${buildingName}-${room} 剩余电量(度)`,
                    data: data,
                    backgroundColor: 'rgba(13, 110, 253, 0.15)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: 'rgba(255, 140, 0, 1)', // 橙色点
                    pointBorderColor: 'rgba(13, 110, 253, 1)',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 10,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 },
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const record = history[index];
                                return [
                                    `电量: ${record.electricity.toFixed(2)}度`,
                                    `时间: ${formatQueryTimeFull(record.query_time)}`
                                ];
                            }
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { padding: 15, boxWidth: 12 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: minValue,
                        max: maxValue,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        title: {
                            display: true,
                            text: '电量(度)',
                            color: '#666',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    x: {
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        title: {
                            display: true,
                            text: '查询时间',
                            color: '#666',
                            font: { size: 12, weight: 'bold' }
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