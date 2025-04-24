// 等待DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 获取最新查询时间
    fetchLatestQueryTime();

    // 获取并显示房间数据
    fetchElectricityData();

    // 获取并显示分析结果
    fetchAnalysisResult();

    // 获取查询历史
    fetchQueryHistory();

    // 获取楼栋数据
    fetchBuildingData();

    // 搜索功能
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('room-search');

    searchButton.addEventListener('click', () => {
        searchRooms();
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchRooms();
        }
    });

    // 添加表格排序功能
    setupTableSorting();
});

// 设置表格排序功能
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th.sortable');

    // 当前排序状态
    window.currentSort = {
        field: 'electricity', // 默认按电量排序
        direction: 'asc'      // 默认升序排列（电量从低到高）
    };

    // 为所有可排序的表头添加点击事件
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const field = header.getAttribute('data-field');

            // 如果点击的是当前排序字段，则切换排序方向
            if (field === window.currentSort.field) {
                window.currentSort.direction = window.currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                // 否则，更新排序字段，并设置为升序
                window.currentSort.field = field;
                window.currentSort.direction = 'asc';
            }

            // 更新表头样式
            updateSortHeaderStyles();

            // 如果数据已加载，则重新排序并显示
            if (window.originalRoomData) {
                const sortedData = sortRoomData([...window.originalRoomData]);
                displayRoomData(sortedData);
            }
        });
    });

    // 初始化表头样式 - 默认按电量升序
    setTimeout(() => {
        updateSortHeaderStyles();
    }, 1000);
}

// 更新表头排序样式
function updateSortHeaderStyles() {
    const headers = document.querySelectorAll('th.sortable');

    headers.forEach(header => {
        const field = header.getAttribute('data-field');

        // 移除所有排序类
        header.classList.remove('sort-asc', 'sort-desc');

        // 为当前排序的字段添加相应的类
        if (field === window.currentSort.field) {
            header.classList.add(window.currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    });
}

// 对房间数据进行排序
function sortRoomData(data) {
    const { field, direction } = window.currentSort;

    return data.sort((a, b) => {
        let valueA, valueB;

        // 根据不同字段获取对应的值
        if (field === 'building') {
            valueA = parseInt(a.building);
            valueB = parseInt(b.building);
        } else if (field === 'room') {
            // 特殊处理房间号排序逻辑
            valueA = parseRoomNumber(a.room);
            valueB = parseRoomNumber(b.room);

            // 如果楼层相同，比较具体的值
            return direction === 'asc'
                ? compareRoomNumbers(valueA, valueB)
                : compareRoomNumbers(valueB, valueA);
        } else if (field === 'electricity') {
            valueA = parseFloat(a.electricity);
            valueB = parseFloat(b.electricity);
        } else if (field === 'status') {
            // 状态的排序逻辑 - 根据电量大小确定状态优先级
            valueA = getStatusPriority(parseFloat(a.electricity));
            valueB = getStatusPriority(parseFloat(b.electricity));
        }

        // 比较逻辑
        if (typeof valueA === 'string' && typeof valueB === 'string') {
            // 字符串比较
            return direction === 'asc'
                ? valueA.localeCompare(valueB, 'zh-CN')
                : valueB.localeCompare(valueA, 'zh-CN');
        } else {
            // 数字比较
            return direction === 'asc' ? valueA - valueB : valueB - valueA;
        }
    });
}

// 解析房间号为数值对象
function parseRoomNumber(roomStr) {
    // 处理形如 "x-yyy" 的房间号
    if (roomStr.includes('-')) {
        const [building, roomNumber] = roomStr.split('-');
        return {
            building: parseInt(building) || 0,
            floor: Math.floor(parseInt(roomNumber) / 100) || 0,
            room: parseInt(roomNumber) % 100 || 0,
            original: roomStr
        };
    }
    // 处理只有数字的房间号 (如 "101")
    else if (/^\d+$/.test(roomStr)) {
        return {
            building: 0,
            floor: Math.floor(parseInt(roomStr) / 100) || 0,
            room: parseInt(roomStr) % 100 || 0,
            original: roomStr
        };
    }
    // 其他情况返回原始字符串
    return {
        building: 0,
        floor: 0,
        room: 0,
        original: roomStr
    };
}

// 比较两个房间号对象
function compareRoomNumbers(roomA, roomB) {
    // 首先比较楼栋
    if (roomA.building !== roomB.building) {
        return roomA.building - roomB.building;
    }

    // 然后比较楼层
    if (roomA.floor !== roomB.floor) {
        return roomA.floor - roomB.floor;
    }

    // 最后比较房间号
    if (roomA.room !== roomB.room) {
        return roomA.room - roomB.room;
    }

    // 如果全部相同，返回原始字符串比较结果
    return roomA.original.localeCompare(roomB.original, 'zh-CN');
}

// 获取状态优先级 (用于排序)
function getStatusPriority(electricity) {
    if (electricity < 10) return 1;      // 紧张
    if (electricity < 50) return 2;      // 一般
    if (electricity < 100) return 3;     // 充足
    return 4;                           // 优秀
}

// 获取最新查询时间
async function fetchLatestQueryTime() {
    try {
        const response = await fetch('/api/latest_query_time');
        const data = await response.json();

        const timeElement = document.getElementById('latest-query-time');
        timeElement.textContent = `最新查询时间: ${data.query_time}`;
    } catch (error) {
        console.error('获取查询时间出错:', error);
        const timeElement = document.getElementById('latest-query-time');
        timeElement.textContent = '最新查询时间: 获取失败';
    }
}

// 获取电量数据
async function fetchElectricityData() {
    try {
        const response = await fetch('/api/electricity_data');
        const data = await response.json();

        if (data.data && data.data.length > 0) {
            // 存储原始数据用于搜索和排序
            window.originalRoomData = data.data;

            // 应用默认排序 - 按电量升序排列
            const sortedData = sortRoomData([...window.originalRoomData]);

            // 显示排序后的数据
            displayRoomData(sortedData);
        } else {
            const roomDataElement = document.getElementById('room-data');
            roomDataElement.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <i class="bi bi-exclamation-circle text-warning" style="font-size: 2rem;"></i>
                        <p class="mt-3">没有找到房间数据</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('获取电量数据出错:', error);
        const roomDataElement = document.getElementById('room-data');
        roomDataElement.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                    <p class="mt-3">获取数据失败: ${error.message}</p>
                </td>
            </tr>
        `;
    }
}

// 显示房间数据
function displayRoomData(roomsData) {
    const roomDataElement = document.getElementById('room-data');

    // 清空现有内容
    roomDataElement.innerHTML = '';

    roomsData.forEach(room => {
        const electricity = parseFloat(room.electricity);
        let status = '';
        let statusClass = '';

        // 根据电量值确定状态
        if (electricity < 10) {
            status = '紧张';
            statusClass = 'status-danger';
        } else if (electricity < 50) {
            status = '一般';
            statusClass = 'status-warning';
        } else if (electricity < 100) {
            status = '充足';
            statusClass = 'status-good';
        } else {
            status = '优秀';
            statusClass = 'status-excellent';
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>新苑${room.building}号楼</td>
            <td>${room.room}</td>
            <td>${electricity.toFixed(2)}</td>
            <td><span class="electricity-status ${statusClass}">${status}</span></td>
        `;

        roomDataElement.appendChild(row);
    });
}

// 获取分析结果
async function fetchAnalysisResult() {
    try {
        const response = await fetch('/api/analysis');
        const data = await response.json();

        const analysisElement = document.getElementById('analysis-result');

        if (data.analysis_lines && data.analysis_lines.length > 0) {
            let htmlContent = '';
            let currentSection = '';

            data.analysis_lines.forEach(line => {
                // 处理标题行
                if (line.includes('电量数据分析')) {
                    htmlContent += `<h4>${line}</h4>`;
                }
                // 处理各个部分的标题
                else if (line.includes('总体数据:')) {
                    currentSection = 'overall';
                    htmlContent += `<div class="analysis-title">${line}</div>`;
                }
                else if (line.includes('各楼栋数据:')) {
                    currentSection = 'building';
                    htmlContent += `<div class="analysis-title">${line}</div>`;
                }
                else if (line.includes('电量区间分布:')) {
                    currentSection = 'distribution';
                    htmlContent += `<div class="analysis-title">${line}</div>`;
                }
                else if (line.includes('各楼层平均电量:')) {
                    currentSection = 'floor';
                    htmlContent += `<div class="analysis-title">${line}</div>`;
                }
                // 空行
                else if (line.trim() === '') {
                    // 不添加内容
                }
                // 处理普通行
                else {
                    htmlContent += `<div class="analysis-item">${line}</div>`;
                }
            });

            analysisElement.innerHTML = htmlContent;
        } else {
            analysisElement.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 2rem;"></i>
                    <p class="mt-3">没有找到分析数据</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('获取分析结果出错:', error);
        const analysisElement = document.getElementById('analysis-result');
        analysisElement.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                <p class="mt-3">获取分析失败: ${error.message}</p>
            </div>
        `;
    }
}

// 获取查询历史
async function fetchQueryHistory() {
    try {
        const response = await fetch('/api/query_history');
        const data = await response.json();

        const historyElement = document.getElementById('query-history');

        if (data.history && data.history.length > 0) {
            let htmlContent = '';

            data.history.forEach(item => {
                htmlContent += `
                    <div class="history-item">
                        <div class="history-desc">${item.description || '批量查询'}</div>
                        <div class="history-time">${item.query_time}</div>
                    </div>
                `;
            });

            historyElement.innerHTML = htmlContent;
        } else {
            historyElement.innerHTML = `
                <div class="text-center py-3">
                    <i class="bi bi-clock text-muted" style="font-size: 1.5rem;"></i>
                    <p class="mt-2">暂无查询历史</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('获取查询历史出错:', error);
        const historyElement = document.getElementById('query-history');
        historyElement.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-exclamation-triangle text-danger" style="font-size: 1.5rem;"></i>
                <p class="mt-2">获取历史失败</p>
            </div>
        `;
    }
}

// 获取楼栋数据
async function fetchBuildingData() {
    try {
        const response = await fetch('/api/building_data');
        const data = await response.json();

        const buildingElement = document.getElementById('building-stats');
        const overallElement = document.getElementById('overall-stats');

        if (data.building_stats && data.building_stats.length > 0) {
            // 显示楼栋数据
            let buildingHtml = '';

            data.building_stats.forEach(building => {
                buildingHtml += `
                    <div class="building-item">
                        <div class="building-title">新苑${building.building}号楼</div>
                        <div class="building-stats">
                            <span>平均: ${building.average.toFixed(2)}度</span>
                            <span>房间: ${building.count}个</span>
                        </div>
                    </div>
                `;
            });

            buildingElement.innerHTML = buildingHtml;

            // 计算总体数据并显示在总体统计区域
            const totalRooms = data.building_stats.reduce((sum, building) => sum + building.count, 0);
            const weightedAvg = data.building_stats.reduce((sum, building) => sum + building.average * building.count, 0) / totalRooms;

            // 找出最低和最高电量的楼栋
            let minBuilding = data.building_stats[0];
            let maxBuilding = data.building_stats[0];

            data.building_stats.forEach(building => {
                if (building.average < minBuilding.average) minBuilding = building;
                if (building.average > maxBuilding.average) maxBuilding = building;
            });

            overallElement.innerHTML = `
                <div class="row">
                    <div class="col-6">
                        <div class="stat-card">
                            <div class="stat-title">总房间数</div>
                            <div class="stat-value">${totalRooms}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-card">
                            <div class="stat-title">平均电量</div>
                            <div class="stat-value">${weightedAvg.toFixed(2)} <small>度</small></div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-6">
                        <div class="stat-card">
                            <div class="stat-title">电量最低楼栋</div>
                            <div class="stat-value">新苑${minBuilding.building}号</div>
                            <div>${minBuilding.average.toFixed(2)} 度</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-card">
                            <div class="stat-title">电量最高楼栋</div>
                            <div class="stat-value">新苑${maxBuilding.building}号</div>
                            <div>${maxBuilding.average.toFixed(2)} 度</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            buildingElement.innerHTML = `
                <div class="text-center py-3">
                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 1.5rem;"></i>
                    <p class="mt-2">暂无楼栋数据</p>
                </div>
            `;

            overallElement.innerHTML = `
                <div class="text-center py-3">
                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 1.5rem;"></i>
                    <p class="mt-2">暂无统计数据</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('获取楼栋数据出错:', error);
        const buildingElement = document.getElementById('building-stats');
        buildingElement.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-exclamation-triangle text-danger" style="font-size: 1.5rem;"></i>
                <p class="mt-2">获取数据失败</p>
            </div>
        `;
    }
}

// 搜索房间
function searchRooms() {
    const searchInput = document.getElementById('room-search');
    const searchTerm = searchInput.value.trim().toLowerCase();

    // 如果没有原始数据，无法搜索
    if (!window.originalRoomData) {
        return;
    }

    // 如果搜索词为空，显示所有数据（按当前排序方式）
    if (searchTerm === '') {
        const sortedData = sortRoomData([...window.originalRoomData]);
        displayRoomData(sortedData);
        return;
    }

    // 过滤符合条件的房间
    const filteredRooms = window.originalRoomData.filter(room => {
        return (
            room.building.toString().includes(searchTerm) ||
            room.room.toLowerCase().includes(searchTerm) ||
            `${room.building}-${room.room}`.toLowerCase().includes(searchTerm)
        );
    });

    // 对过滤后的结果应用排序
    const sortedFilteredRooms = sortRoomData([...filteredRooms]);

    // 显示排序后的过滤结果
    displayRoomData(sortedFilteredRooms);

    // 显示搜索结果数量
    const roomDataElement = document.getElementById('room-data');
    if (filteredRooms.length === 0) {
        roomDataElement.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-search text-muted" style="font-size: 2rem;"></i>
                    <p class="mt-3">未找到匹配 "${searchTerm}" 的房间</p>
                </td>
            </tr>
        `;
    }
} 