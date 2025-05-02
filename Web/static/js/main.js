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

    // 获取历史电量查询时间点
    fetchHistoryTimes();

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

    // 添加调试按钮功能
    const debugBtn = document.getElementById('debug-btn');
    if (debugBtn) {
        debugBtn.addEventListener('click', showDebugModal);
    }

    // 添加修复数据按钮功能
    const fixDataBtn = document.getElementById('fix-data-btn');
    if (fixDataBtn) {
        fixDataBtn.addEventListener('click', fixHistoryData);
    }

    // 添加宿舍历史电量图表模态框功能
    setupRoomHistoryFeature();

    // 添加历史选择器查询按钮的点击事件
    const applyHistorySelectorBtn = document.getElementById('apply-history-selector');
    if (applyHistorySelectorBtn) {
        applyHistorySelectorBtn.addEventListener('click', function () {
            const selector = document.getElementById('history-selector');
            if (!selector) {
                console.error("找不到历史选择器元素");
                return;
            }

            const selectedValue = selector.value;
            const selectedIndex = selector.selectedIndex;
            const selectedOption = selector.options[selectedIndex];

            console.log("-------- 点击查询按钮 --------");
            console.log(`选择器值: [${selectedValue}]`);
            console.log(`选中索引: ${selectedIndex}`);
            console.log(`选中文本: "${selectedOption ? selectedOption.textContent : '未知'}"`);

            // 再次验证所有选项
            console.log("所有选项:");
            for (let i = 0; i < selector.options.length; i++) {
                const opt = selector.options[i];
                console.log(`  #${i}: value=[${opt.value}], text=[${opt.textContent}]`);
            }

            if (selectedValue === 'latest') {
                console.log("选择了最新数据，调用fetchElectricityData()");
                fetchElectricityData();
                return;
            }

            if (!selectedValue || selectedValue === 'undefined' || selectedValue === 'debug') {
                console.error(`选择器值无效: ${selectedValue}`);
                alert('请选择一个有效的历史时间点');
                return;
            }

            // 验证是否为数字
            if (!/^\d+$/.test(selectedValue)) {
                console.error(`选中的值不是纯数字: ${selectedValue}`);
                alert(`选择器值格式不正确: ${selectedValue} (应为纯数字)`);
                return;
            }

            // 构建API URL
            const apiUrl = `/api/history_data/${selectedValue}`;
            console.log(`构建API URL: ${apiUrl}`);

            // 显示加载状态
            const roomDataElement = document.getElementById('room-data');
            roomDataElement.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="mt-3">正在加载历史数据...</p>
                        <p class="small text-muted">时间ID: ${selectedValue}</p>
                        <p class="small text-muted">API URL: ${apiUrl}</p>
                    </td>
                </tr>
            `;

            // 使用fetch直接请求
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    console.log("API直接调用返回:", data);

                    // 若API返回了错误
                    if (data.error) {
                        console.error(`API返回错误: ${data.error}`);
                        roomDataElement.innerHTML = `
                            <tr>
                                <td colspan="4" class="text-center py-5">
                                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                                    <p class="mt-3">获取历史数据错误: ${data.error}</p>
                                    <p class="small text-muted">时间ID: ${selectedValue}</p>
                                    <p class="small text-muted">API URL: ${apiUrl}</p>
                                    <pre class="text-start" style="max-height:200px;overflow:auto;font-size:12px;">调试信息:
${JSON.stringify(data.debug_info || {}, null, 2)}</pre>
                                </td>
                            </tr>
                        `;
                        updateDisplayTime('获取失败', true);
                        return;
                    }

                    // 处理成功的响应
                    const queryTime = data.query_time || '未知时间';
                    console.log(`显示时间: ${queryTime}`);
                    updateDisplayTime(queryTime, true);

                    if (data.data && data.data.length > 0) {
                        console.log(`获取到 ${data.data.length} 条记录`);
                        window.originalRoomData = data.data;
                        const sortedData = sortRoomData([...window.originalRoomData]);
                        displayRoomData(sortedData);
                    } else {
                        console.log("API返回的数据为空");
                        roomDataElement.innerHTML = `
                            <tr>
                                <td colspan="4" class="text-center py-5">
                                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 2rem;"></i>
                                    <p class="mt-3">该时间点没有电量数据</p>
                                    <p class="small text-muted">时间ID: ${selectedValue}</p>
                                </td>
                            </tr>
                        `;
                    }
                })
                .catch(error => {
                    console.error("API请求出错:", error);
                    roomDataElement.innerHTML = `
                        <tr>
                            <td colspan="4" class="text-center py-5">
                                <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                                <p class="mt-3">API请求失败: ${error.message}</p>
                                <p class="small text-muted">时间ID: ${selectedValue}</p>
                                <p class="small text-muted">API URL: ${apiUrl}</p>
                            </td>
                        </tr>
                    `;
                    updateDisplayTime('请求失败', true);
                });
        });
    } else {
        console.error("找不到历史选择器查询按钮");
    }

    // 添加"使用选择器值"按钮事件
    const useSelectorValueBtn = document.getElementById('use-selector-value');
    if (useSelectorValueBtn) {
        useSelectorValueBtn.addEventListener('click', function () {
            const selector = document.getElementById('history-selector');
            const timeIdInput = document.getElementById('test-time-id');

            if (selector && timeIdInput) {
                const selectorValue = selector.value;
                if (selectorValue && selectorValue !== 'latest' && selectorValue !== 'undefined') {
                    timeIdInput.value = selectorValue;
                    console.log(`已将选择器值 [${selectorValue}] 复制到测试输入框`);
                } else {
                    alert('当前选择器值不适合用于API测试');
                }
            }
        });
    }

    // 监控选择器值变化，更新显示
    const historySelector = document.getElementById('history-selector');
    if (historySelector) {
        const updateSelectorValue = function () {
            const valueDisplay = document.querySelector('#current-selector-value span');
            if (valueDisplay) {
                valueDisplay.textContent = historySelector.value || 'undefined';
            }
        };

        // 初始显示
        updateSelectorValue();

        // 监听变化
        historySelector.addEventListener('change', updateSelectorValue);
    }

    // 添加历史选择器调试按钮的事件监听
    const debugSelectorBtn = document.getElementById('debug-selector');
    if (debugSelectorBtn) {
        debugSelectorBtn.addEventListener('click', function () {
            const selector = document.getElementById('history-selector');
            if (!selector) {
                alert('找不到历史选择器元素!');
                return;
            }

            // 获取调试结果区域
            const resultDiv = document.getElementById('api-test-result');
            if (resultDiv) {
                resultDiv.innerHTML = '<div class="alert alert-info">正在分析选择器...</div>';

                // 分析选择器
                let html = '<div class="alert alert-secondary">';
                html += `<p><strong>选择器ID:</strong> ${selector.id}</p>`;
                html += `<p><strong>选项数量:</strong> ${selector.options.length}</p>`;
                html += `<p><strong>当前选中:</strong> index=${selector.selectedIndex}, value=${selector.value}</p>`;

                html += '<p><strong>所有选项:</strong></p><ul class="list-group">';
                for (let i = 0; i < selector.options.length; i++) {
                    const option = selector.options[i];
                    const isSelected = i === selector.selectedIndex;
                    html += `<li class="list-group-item ${isSelected ? 'active' : ''}">
                        <strong>#${i}:</strong> value="${option.value}", 
                        text="${option.textContent}"
                        ${option.disabled ? '(disabled)' : ''}
                    </li>`;
                }
                html += '</ul>';

                html += '</div>';
                resultDiv.innerHTML = html;

                // 打印到控制台
                console.group('选择器调试信息');
                console.log('选择器:', selector);
                console.log('选项数量:', selector.options.length);
                console.log('当前选中索引:', selector.selectedIndex);
                console.log('当前选中值:', selector.value);

                console.log('所有选项:');
                for (let i = 0; i < selector.options.length; i++) {
                    const option = selector.options[i];
                    console.log(`  #${i}: value=[${option.value}], text=[${option.textContent}], disabled=${option.disabled}`);
                }
                console.groupEnd();
            }
        });
    }

    // 直接测试API按钮
    document.getElementById('test-direct-api').addEventListener('click', async function () {
        try {
            const timeIdInput = document.getElementById('test-time-id');
            const timeId = timeIdInput.value.trim();
            const resultDiv = document.getElementById('api-test-result');

            if (!timeId) {
                if (resultDiv) resultDiv.innerHTML = '<div class="alert alert-danger">请输入Time ID</div>';
                alert('请输入Time ID');
                return;
            }

            console.log(`直接测试API，使用time_id=${timeId}`);

            if (resultDiv) {
                resultDiv.innerHTML = `
                    <div class="alert alert-info">
                        <div class="d-flex align-items-center">
                            <div class="spinner-border spinner-border-sm me-2" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <div>正在测试: /api/history_data/${timeId}</div>
                        </div>
                    </div>
                `;
            }

            // 发送请求
            const response = await fetch(`/api/history_data/${timeId}`);
            const data = await response.json();

            console.log('API返回数据:', data);

            // 更新结果显示
            if (resultDiv) {
                if (data.error) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <p><strong>错误:</strong> ${data.error}</p>
                            <p><strong>查询时间:</strong> ${data.query_time || '未知'}</p>
                            <p><strong>调试信息:</strong></p>
                            <pre>${JSON.stringify(data.debug_info || {}, null, 2)}</pre>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <p><strong>成功!</strong> 获取了 ${data.data ? data.data.length : 0} 条记录</p>
                            <p><strong>查询时间:</strong> ${data.query_time || '未知'}</p>
                            <button class="btn btn-sm btn-primary mt-2" id="apply-test-result">应用到表格</button>
                        </div>
                    `;

                    // 添加应用结果按钮事件
                    document.getElementById('apply-test-result').addEventListener('click', function () {
                        if (data.data && data.data.length > 0) {
                            try {
                                window.originalRoomData = data.data;
                                const sortedData = sortRoomData([...window.originalRoomData]);
                                displayRoomData(sortedData);
                                updateDisplayTime(data.query_time || '未知时间', true);
                                alert('数据已成功应用到表格');
                            } catch (e) {
                                console.error('应用数据出错:', e);
                                alert('应用数据出错: ' + e.message);
                            }
                        } else {
                            alert('API返回的数据为空，无法应用');
                        }
                    });
                }
            }
        } catch (error) {
            console.error('直接测试API出错:', error);
            if (resultDiv) {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <p><strong>错误:</strong> ${error.message}</p>
                        <p><strong>调试信息:</strong></p>
                        <pre>${JSON.stringify(error.debug_info || {}, null, 2)}</pre>
                    </div>
                `;
            }
        }
    });
});

// 设置表格排序功能
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th.sortable');

    // 当前排序状态
    window.currentSort = {
        field: 'room', // 默认按房间号排序（修改为房间号）
        direction: 'asc'      // 默认升序排列
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

    // 初始化表头样式 - 修改为默认按房间号升序
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

        updateDisplayTime(data.query_time);
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

        // 更新时间显示为最新查询时间
        updateDisplayTime(data.query_time);

        if (data.data && data.data.length > 0) {
            // 存储原始数据用于搜索和排序
            window.originalRoomData = data.data;

            // 应用当前排序设置 - 使用当前排序字段和方向
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

        // 为每行添加点击事件，点击后显示该宿舍的历史电量数据
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            showRoomHistory(room.building, room.room);
        });

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

// 获取历史电量查询时间点
async function fetchHistoryTimes() {
    try {
        console.log("开始获取历史时间点...");

        // 获取选择器元素
        const historySelector = document.getElementById('history-selector');
        if (!historySelector) {
            console.error("找不到历史选择器元素");
            return;
        }

        // 修改选择器的change事件，仅显示日志而不直接触发API调用
        historySelector.addEventListener('change', function () {
            const value = this.value;
            const selectedOption = this.options[this.selectedIndex];
            console.log(`选择器变更: 选择了 [${value}], 文本=[${selectedOption ? selectedOption.textContent : '未知'}]`);

            // 禁用自动触发
            // 现在用户需要点击旁边的按钮来执行查询
        });

        // 获取容器元素
        const container = document.querySelector('.history-selector-container');
        if (!container) {
            console.error("找不到历史选择器容器");
            return;
        }

        // 创建一个新的选择器元素
        const newSelector = document.createElement('select');
        newSelector.id = 'history-selector';
        newSelector.className = 'form-select form-select-sm';

        // 添加"最新数据"选项
        const latestOption = document.createElement('option');
        latestOption.value = 'latest';
        latestOption.textContent = '最新数据';
        latestOption.selected = true;
        newSelector.appendChild(latestOption);

        // 添加"加载中"选项
        const loadingOption = document.createElement('option');
        loadingOption.disabled = true;
        loadingOption.textContent = '正在加载历史数据...';
        newSelector.appendChild(loadingOption);

        // 获取历史时间点数据前先替换选择器
        container.innerHTML = '';
        container.appendChild(newSelector);

        // 添加选择器事件监听，仅记录选择的值，不触发API调用
        newSelector.addEventListener('change', function () {
            const value = this.value;
            console.log(`选择器变更: 选择了 [${value}]`);
            console.log(`选中的值类型: ${typeof value}, 长度: ${value ? value.length : 'undefined'}`);

            // 记录选中的选项详情
            const selectedOption = this.options[this.selectedIndex];
            console.log(`选中的选项: index=${this.selectedIndex}, text='${selectedOption.textContent}'`);

            // 记录所有选项的值，以便调试
            console.log("所有选项的值:");
            for (let i = 0; i < this.options.length; i++) {
                const opt = this.options[i];
                console.log(`  #${i}: value=[${opt.value}], text=[${opt.textContent}]`);
            }

            // 不再自动触发API调用，需要用户点击查询按钮
        });

        // 获取历史时间点数据
        console.log("请求API: /api/history_times");
        const response = await fetch('/api/history_times');
        const data = await response.json();
        console.log("API返回数据:", data);

        // 清除加载中选项
        while (newSelector.options.length > 1) {
            newSelector.remove(1);
        }

        // 添加历史时间点选项
        if (data.history_times && data.history_times.length > 0) {
            console.log(`找到 ${data.history_times.length} 个历史时间点`);

            data.history_times.forEach((item, index) => {
                // 获取日期时间字符串并转换为timeId
                let timeId;
                let displayText;

                if (item.query_time) {
                    // 从显示的时间中提取数字，例如从"2025-05-02 13:30:01"提取"202505021330"
                    const dateMatch = item.query_time.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/);
                    if (dateMatch) {
                        // 提取年月日时分
                        const [_, year, month, day, hour, minute] = dateMatch;
                        timeId = `${year}${month}${day}${hour}${minute}`;
                        displayText = item.description || item.query_time;
                    } else {
                        // 如果匹配失败，跳过此项
                        console.warn(`无法从 ${item.query_time} 提取日期时间格式，跳过该选项`);
                        return;
                    }
                } else if (item.time_id && item.time_id !== 'undefined') {
                    // 如果有time_id，直接使用
                    timeId = item.time_id;
                    displayText = item.description || '历史数据';
                } else {
                    // 如果没有有效数据，跳过
                    console.warn(`跳过无效的时间点 #${index}:`, item);
                    return;
                }

                // 验证timeId
                if (!timeId || timeId === 'undefined') {
                    console.warn(`生成的timeId无效: ${timeId}，跳过`);
                    return;
                }

                // 确保timeId是字符串并且只包含数字
                const timeIdStr = String(timeId).trim();
                if (!/^\d+$/.test(timeIdStr)) {
                    console.warn(`timeId不是纯数字: ${timeIdStr}，跳过`);
                    return;
                }

                // 创建选项
                const option = document.createElement('option');
                option.value = timeIdStr;
                option.textContent = displayText;

                // 添加到选择器
                newSelector.appendChild(option);

                console.log(`添加选项 #${index}: value=[${option.value}], text=[${option.textContent}]`);
            });

            // 添加调试按钮
            const debugButton = document.createElement('button');
            debugButton.type = 'button';
            debugButton.className = 'btn btn-sm btn-outline-secondary mt-2';
            debugButton.textContent = '调试选择器';
            debugButton.style.width = '100%';
            debugButton.addEventListener('click', function () {
                const selector = document.getElementById('history-selector');
                if (!selector) {
                    alert('找不到选择器元素!');
                    return;
                }

                console.group('选择器调试信息');
                console.log("当前选择器值:", selector.value);
                console.log("选择器选项数量:", selector.options.length);

                console.log("所有选项:");
                for (let i = 0; i < selector.options.length; i++) {
                    const opt = selector.options[i];
                    console.log(`  #${i}: value=[${opt.value}], text=[${opt.textContent}]`);
                }

                const selectedOption = selector.options[selector.selectedIndex];
                console.log("当前选中:", selectedOption ?
                    `index=${selector.selectedIndex}, value=[${selectedOption.value}], text=[${selectedOption.textContent}]` :
                    "未选中任何选项");
                console.groupEnd();

                alert("选择器调试信息已打印到控制台");
            });

            container.appendChild(debugButton);
        } else {
            // 添加"暂无历史数据"选项
            const noDataOption = document.createElement('option');
            noDataOption.disabled = true;
            noDataOption.textContent = '暂无历史数据';
            newSelector.appendChild(noDataOption);
            console.warn("没有找到历史时间点数据");
        }
    } catch (error) {
        console.error('获取历史时间点出错:', error);

        // 如果出错，添加错误选项
        const historySelector = document.getElementById('history-selector');
        if (historySelector) {
            // 清除现有选项（除了"最新数据"）
            while (historySelector.options.length > 1) {
                historySelector.remove(1);
            }

            // 添加错误选项
            const errorOption = document.createElement('option');
            errorOption.disabled = true;
            errorOption.textContent = '加载失败: ' + error.message;
            historySelector.appendChild(errorOption);
        }
    }
}

// 获取指定时间点的历史电量数据
async function fetchHistoryData(timeId) {
    try {
        console.log("--------- 开始获取历史数据 ---------");
        console.log("获取历史数据函数被调用，参数timeId =", timeId);
        console.log("timeId的类型:", typeof timeId);
        console.log("timeId的长度:", timeId ? timeId.length : 'undefined');

        if (timeId) {
            console.log("timeId是否是数字:", /^\d+$/.test(timeId));
            console.log("timeId的每个字符:", Array.from(timeId).map(c => `${c}(${c.charCodeAt(0)})`).join(', '));
        }

        // 备份原始timeId
        const originalTimeId = timeId;

        // 检查参数，如果无效，尝试从选择器获取
        if (!timeId || timeId === 'undefined' || timeId === 'null') {
            const selector = document.getElementById('history-selector');
            if (selector && selector.value && selector.value !== 'latest' && selector.value !== 'undefined') {
                timeId = selector.value;
                console.log("从选择器获取timeId =", timeId);
            } else {
                console.error("无法获取有效的timeId");

                // 显示错误信息
                const roomDataElement = document.getElementById('room-data');
                roomDataElement.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5">
                            <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                            <p class="mt-3">无效的时间ID</p>
                            <p class="small text-muted">原始timeId = ${originalTimeId}</p>
                            <p class="small text-muted">选择器值 = ${selector ? selector.value : '选择器不存在'}</p>
                        </td>
                    </tr>
                `;
                updateDisplayTime('无效的查询日期', true);
                return;
            }
        }

        // 如果是latest，则获取最新数据
        if (timeId === 'latest') {
            console.log("选择了最新数据，调用fetchElectricityData()");
            fetchElectricityData();
            return;
        }

        // 显示加载状态
        const roomDataElement = document.getElementById('room-data');
        roomDataElement.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-3">正在加载历史数据...</p>
                    <p class="small text-muted">时间ID: ${timeId}</p>
                </td>
            </tr>
        `;

        console.log(`准备请求API: /api/history_data/${timeId}`);

        // 清理和编码timeId
        const cleanedTimeId = String(timeId).trim();
        // 确保timeId全是数字
        if (!/^\d+$/.test(cleanedTimeId)) {
            console.error(`timeId不是纯数字，无法继续: ${cleanedTimeId}`);
            // 显示错误信息
            roomDataElement.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                        <p class="mt-3">时间ID格式不正确: 必须是纯数字</p>
                        <p class="small text-muted">时间ID: ${cleanedTimeId}</p>
                    </td>
                </tr>
            `;
            updateDisplayTime('无效的查询日期', true);
            return;
        }

        const encodedTimeId = encodeURIComponent(cleanedTimeId);
        console.log(`编码后的timeId: ${encodedTimeId}`);

        // 请求历史数据
        const response = await fetch(`/api/history_data/${encodedTimeId}`);
        const data = await response.json();

        console.log("API返回数据:", data);

        // 检查是否有错误
        if (data.error) {
            console.error("API返回错误:", data.error);
            roomDataElement.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                        <p class="mt-3">获取历史数据错误: ${data.error}</p>
                        <p class="small text-muted">时间ID: ${timeId}</p>
                        ${data.debug_info ? `<p class="small text-muted">调试信息: ${JSON.stringify(data.debug_info)}</p>` : ''}
                    </td>
                </tr>
            `;
            updateDisplayTime('获取失败', true);
            return;
        }

        // 确保query_time存在
        const queryTime = data.query_time || '未知时间';
        console.log("显示时间:", queryTime);

        // 更新时间显示
        updateDisplayTime(queryTime, true);

        // 检查数据
        if (data.data && data.data.length > 0) {
            console.log(`获取到 ${data.data.length} 条数据`);

            // 存储数据用于搜索和排序
            window.originalRoomData = data.data;

            // 应用当前排序设置
            const sortedData = sortRoomData([...window.originalRoomData]);

            // 显示排序后的数据
            displayRoomData(sortedData);
        } else {
            console.log("没有获取到数据");
            roomDataElement.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <i class="bi bi-exclamation-circle text-warning" style="font-size: 2rem;"></i>
                        <p class="mt-3">该时间点没有电量数据</p>
                        <p class="small text-muted">时间ID: ${timeId}</p>
                    </td>
                </tr>
            `;
        }

        console.log("--------- 历史数据获取完成 ---------");
    } catch (error) {
        console.error('获取历史电量数据出错:', error);

        const roomDataElement = document.getElementById('room-data');
        roomDataElement.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                    <p class="mt-3">获取历史数据失败: ${error.message}</p>
                </td>
            </tr>
        `;

        updateDisplayTime('获取失败', true);
    }
}

// 更新显示的时间信息
function updateDisplayTime(queryTime, isHistorical = false) {
    const timeElement = document.getElementById('latest-query-time');
    if (isHistorical) {
        timeElement.textContent = `历史数据: ${queryTime}`;
        timeElement.classList.add('text-warning');
    } else {
        timeElement.textContent = `最新查询时间: ${queryTime}`;
        timeElement.classList.remove('text-warning');
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

    // 对过滤后的结果应用当前排序设置
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

// 修复历史数据问题
async function fixHistoryData() {
    try {
        // 修改按钮状态为加载中
        const fixDataBtn = document.getElementById('fix-data-btn');
        const originalText = fixDataBtn.textContent;
        fixDataBtn.disabled = true;
        fixDataBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 修复中...`;

        // 添加状态提示
        const diagnosisInfo = document.getElementById('diagnosis-info');
        diagnosisInfo.innerHTML = `
            <div class="alert alert-info">
                <h5 class="alert-heading">正在修复数据问题...</h5>
                <p>请稍候，系统正在尝试修复历史数据问题。</p>
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" aria-valuenow="100" aria-valuemin="0" 
                         aria-valuemax="100" style="width: 100%"></div>
                </div>
            </div>
        `;

        // 调用修复API
        const response = await fetch('/api/fix_history_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        // 恢复按钮状态
        fixDataBtn.disabled = false;
        fixDataBtn.textContent = originalText;

        // 显示修复结果
        if (result.success) {
            diagnosisInfo.innerHTML = `
                <div class="alert alert-success">
                    <h5 class="alert-heading">修复成功!</h5>
                    <p>${result.message}</p>
                    <hr>
                    <p class="mb-0">建议刷新页面或重新启动应用以应用修复。</p>
                </div>
                <button class="btn btn-primary mt-2" onclick="location.reload()">刷新页面</button>
            `;

            // 重新加载历史时间点
            setTimeout(() => {
                fetchHistoryTimes();
            }, 1000);
        } else {
            let errorDetails = '';
            if (result.errors && result.errors.length > 0) {
                errorDetails = `
                    <hr>
                    <p>错误详情:</p>
                    <ul>
                        ${result.errors.map(err => `<li>${err}</li>`).join('')}
                    </ul>
                `;
            }

            diagnosisInfo.innerHTML = `
                <div class="alert alert-danger">
                    <h5 class="alert-heading">修复失败</h5>
                    <p>${result.message}</p>
                    ${errorDetails}
                    <hr>
                    <p class="mb-0">请检查数据库结构和权限，或尝试手动修复。</p>
                </div>
            `;
        }
    } catch (error) {
        // 处理异常
        console.error('修复数据出错:', error);

        // 恢复按钮状态
        const fixDataBtn = document.getElementById('fix-data-btn');
        fixDataBtn.disabled = false;
        fixDataBtn.textContent = '修复数据';

        // 显示错误信息
        const diagnosisInfo = document.getElementById('diagnosis-info');
        diagnosisInfo.innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading">修复过程出错</h5>
                <p>错误信息: ${error.message}</p>
                <hr>
                <p class="mb-0">请检查网络连接或服务器日志。</p>
            </div>
        `;
    }
}

// 显示调试模态框
function showDebugModal() {
    // 获取模态框元素
    const debugModal = new bootstrap.Modal(document.getElementById('debugModal'));
    debugModal.show();

    // 显示加载状态
    document.getElementById('debug-loading').style.display = 'block';
    document.getElementById('debug-content').style.display = 'none';

    // 获取数据库调试信息
    fetchDebugInfo();
}

// 获取数据库调试信息
async function fetchDebugInfo() {
    try {
        const response = await fetch('/api/debug/database_info');
        const data = await response.json();

        // 隐藏加载状态，显示内容
        document.getElementById('debug-loading').style.display = 'none';
        document.getElementById('debug-content').style.display = 'block';

        // 填充表信息
        const tablesInfo = document.getElementById('tables-info');
        if (data.tables && data.tables.length > 0) {
            tablesInfo.innerHTML = `
                <div class="alert alert-info">
                    <p>数据库中的表 (${data.tables.length} 个):</p>
                    <ul class="mb-0">
                        ${data.tables.map(table => `<li>${table}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else {
            tablesInfo.innerHTML = '<div class="alert alert-warning">未发现数据表</div>';
        }

        // 填充电量历史表结构信息
        const columnsInfo = document.getElementById('columns-info');
        if (data.electricity_history_columns) {
            const regularColumns = data.electricity_history_columns.filter(col => !col.startsWith('e_'));
            const dynamicColumns = data.electricity_history_columns.filter(col => col.startsWith('e_'));

            columnsInfo.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header">基本列 (${regularColumns.length})</div>
                            <div class="card-body">
                                <ul class="list-group">
                                    ${regularColumns.map(col => `<li class="list-group-item">${col}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">电量数据列 (${dynamicColumns.length})</div>
                            <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                                <ul class="list-group">
                                    ${dynamicColumns.map(col => {
                const count = data.dynamic_column_counts ? data.dynamic_column_counts[col] : '未知';
                return `<li class="list-group-item d-flex justify-content-between align-items-center">
                                            ${col}
                                            <span class="badge bg-primary rounded-pill">${count} 条数据</span>
                                        </li>`;
            }).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="alert alert-info mt-3">
                    <p>表中总共有 ${data.electricity_history_count || '未知'} 条记录</p>
                </div>
            `;
        } else {
            columnsInfo.innerHTML = '<div class="alert alert-warning">未发现电量历史表或无法获取列信息</div>';
        }

        // 填充查询历史信息
        const queriesInfo = document.getElementById('queries-info');
        if (data.sample_data && data.sample_data.query_history) {
            const queryHistory = data.sample_data.query_history;
            queriesInfo.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>查询时间</th>
                                <th>描述</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${queryHistory.map(query => `
                                <tr>
                                    <td>${query.id}</td>
                                    <td>${query.query_time}</td>
                                    <td>${query.description || ''}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            queriesInfo.innerHTML = '<div class="alert alert-warning">未发现查询历史数据</div>';
        }

        // 填充示例数据信息
        const dataInfo = document.getElementById('data-info');
        if (data.sample_data && data.sample_data.electricity_history) {
            const sampleData = data.sample_data.electricity_history;
            if (sampleData.length > 0) {
                const firstRow = sampleData[0];
                const allColumns = Object.keys(firstRow);

                dataInfo.innerHTML = `
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    ${allColumns.map(col => `<th>${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${sampleData.map(row => `
                                    <tr>
                                        ${allColumns.map(col => `<td>${row[col] !== null ? row[col] : '空'}</td>`).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                dataInfo.innerHTML = '<div class="alert alert-warning">电量历史表中没有数据</div>';
            }
        } else {
            dataInfo.innerHTML = '<div class="alert alert-warning">未能获取示例数据</div>';
        }

        // 填充问题诊断信息
        const diagnosisInfo = document.getElementById('diagnosis-info');
        diagnosisInfo.innerHTML = '';

        // 检查是否存在查询历史表
        if (!data.tables || !data.tables.includes('query_history')) {
            diagnosisInfo.innerHTML += `
                <div class="alert alert-danger mb-3">
                    <h5 class="alert-heading">问题：缺少查询历史表</h5>
                    <p>数据库中不存在 query_history 表，这是存储查询时间点的必要表。</p>
                    <hr>
                    <p class="mb-0">解决方案：请确保已经通过GUI界面执行过"查询所有宿舍"操作，这将自动创建表结构。</p>
                </div>
            `;
        }

        // 检查是否存在电量历史表
        if (!data.tables || !data.tables.includes('electricity_history')) {
            diagnosisInfo.innerHTML += `
                <div class="alert alert-danger mb-3">
                    <h5 class="alert-heading">问题：缺少电量历史表</h5>
                    <p>数据库中不存在 electricity_history 表，这是存储电量数据的必要表。</p>
                    <hr>
                    <p class="mb-0">解决方案：请确保已经通过GUI界面执行过"查询所有宿舍"操作，这将自动创建表结构。</p>
                </div>
            `;
        }

        // 检查查询历史表中是否有数据
        if (data.sample_data && data.sample_data.query_history && data.sample_data.query_history.length === 0) {
            diagnosisInfo.innerHTML += `
                <div class="alert alert-warning mb-3">
                    <h5 class="alert-heading">问题：查询历史表为空</h5>
                    <p>查询历史表中没有数据，这意味着没有记录电量查询的时间点。</p>
                    <hr>
                    <p class="mb-0">解决方案：请通过GUI界面执行"查询所有宿舍"操作，这将记录查询时间点。</p>
                </div>
            `;
        }

        // 检查电量历史表中的动态列
        if (data.dynamic_columns && data.dynamic_columns.length === 0) {
            diagnosisInfo.innerHTML += `
                <div class="alert alert-warning mb-3">
                    <h5 class="alert-heading">问题：电量历史表缺少电量数据列</h5>
                    <p>电量历史表中没有任何以"e_"开头的动态列，这些列用于存储不同时间点的电量数据。</p>
                    <hr>
                    <p class="mb-0">解决方案：请确保在通过GUI界面执行"查询所有宿舍"后，电量数据被正确保存。</p>
                </div>
            `;
        }

        // 检查最新查询对应的列是否存在
        if (data.expected_column && !data.column_exists) {
            diagnosisInfo.innerHTML += `
                <div class="alert alert-danger mb-3">
                    <h5 class="alert-heading">问题：数据列不匹配</h5>
                    <p>最新查询时间对应的列名 ${data.expected_column} 在电量历史表中不存在。</p>
                    <hr>
                    <p class="mb-0">解决方案：检查查询历史表和电量历史表的同步问题，可能是由于时间格式转换错误导致的。</p>
                </div>
            `;
        }

        // 检查是否所有的动态列都没有数据
        if (data.dynamic_column_counts) {
            const allEmpty = Object.values(data.dynamic_column_counts).every(count => count === 0);
            if (allEmpty && Object.keys(data.dynamic_column_counts).length > 0) {
                diagnosisInfo.innerHTML += `
                    <div class="alert alert-danger mb-3">
                        <h5 class="alert-heading">问题：所有电量数据列都为空</h5>
                        <p>所有电量数据列都不包含任何非空值，这可能是由于数据保存失败导致的。</p>
                        <hr>
                        <p class="mb-0">解决方案：检查数据保存过程中的错误，或尝试重新执行"查询所有宿舍"操作。</p>
                    </div>
                `;
            }
        }

        // 如果没有发现任何问题
        if (diagnosisInfo.innerHTML === '') {
            diagnosisInfo.innerHTML = `
                <div class="alert alert-success">
                    <h5 class="alert-heading">未发现明显问题</h5>
                    <p>数据库结构和数据看起来是正常的。如果界面仍然显示"该时间点没有电量数据"，可能是因为：</p>
                    <ul>
                        <li>选择的时间点确实没有电量数据</li>
                        <li>数据格式转换问题</li>
                        <li>前端代码错误</li>
                    </ul>
                    <hr>
                    <p class="mb-0">建议：请尝试重新执行一次"查询所有宿舍"操作，然后刷新页面后重试。</p>
                </div>
            `;
        }

    } catch (error) {
        console.error('获取调试信息出错:', error);
        document.getElementById('debug-loading').style.display = 'none';
        document.getElementById('debug-content').style.display = 'block';

        // 显示错误信息
        document.getElementById('diagnosis-info').innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading">获取调试信息失败</h5>
                <p>错误信息: ${error.message}</p>
                <hr>
                <p class="mb-0">请检查服务器日志或尝试重启应用。</p>
            </div>
        `;
    }
}

// 设置宿舍历史电量相关功能
function setupRoomHistoryFeature() {
    // 如果有任何初始化工作，可以在这里完成
    console.log('宿舍历史电量功能已初始化');
}

// 显示宿舍历史电量数据模态框
function showRoomHistory(building, room) {
    // 获取模态框并显示
    const modal = new bootstrap.Modal(document.getElementById('roomHistoryModal'));
    modal.show();

    // 显示房间信息
    document.getElementById('room-history-title').textContent = `新苑${building}号楼 - ${room}`;

    // 显示加载状态
    document.getElementById('room-history-loading').style.display = 'block';
    document.getElementById('room-history-content').style.display = 'none';
    document.getElementById('room-history-error').style.display = 'none';

    // 获取宿舍历史电量数据
    fetchRoomHistoryData(building, room);
}

// 获取宿舍历史电量数据
function fetchRoomHistoryData(building, room) {
    // 显示加载状态
    document.getElementById('room-history-loading').style.display = 'block';
    document.getElementById('room-history-content').style.display = 'none';
    document.getElementById('room-history-error').style.display = 'none';

    // 获取房间历史数据
    fetch(`/api/room_history/${building}/${room}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`请求失败，状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            if (data.history && data.history.length > 0) {
                // 计算消耗电量
                calculateConsumption(data.history);
                // 显示数据
                displayRoomHistoryData(data.history);
            } else {
                throw new Error('没有找到历史数据');
            }
        })
        .catch(error => {
            console.error('获取房间历史数据时出错:', error);
            document.getElementById('room-history-loading').style.display = 'none';
            document.getElementById('room-history-error').style.display = 'block';
            document.getElementById('room-history-error').textContent = `获取历史数据失败: ${error.message}`;
        });
}

// 计算消耗电量
function calculateConsumption(data) {
    try {
        // 验证输入数据
        if (!Array.isArray(data) || data.length === 0) {
            console.warn('没有数据可以计算消耗电量');
            return;
        }

        // 按时间从早到晚排序
        const sortedData = [...data].sort((a, b) => new Date(a.query_time) - new Date(b.query_time));

        // 计算相邻数据点之间的消耗量
        for (let i = 1; i < sortedData.length; i++) {
            const prevRecord = sortedData[i - 1];
            const currRecord = sortedData[i];

            if (!prevRecord.electricity || !currRecord.electricity) {
                currRecord.consumption = null;
                continue;
            }

            const prevElectricity = parseFloat(prevRecord.electricity);
            const currElectricity = parseFloat(currRecord.electricity);

            if (isNaN(prevElectricity) || isNaN(currElectricity)) {
                currRecord.consumption = null;
                continue;
            }

            // 如果前一个电量大于当前电量，说明期间有消耗
            if (prevElectricity > currElectricity) {
                // 计算消耗量
                currRecord.consumption = (prevElectricity - currElectricity).toFixed(2);
            } else {
                // 如果电量增加或不变，可能是充值了或者没有用电
                currRecord.consumption = '0.00';
            }
        }

        // 第一个数据点没有前一个点，不能计算消耗
        if (sortedData.length > 0) {
            sortedData[0].consumption = null;
        }
    } catch (error) {
        console.error('计算消耗电量时出错:', error);
    }
}

// 显示房间历史数据
function displayRoomHistoryData(historyData) {
    try {
        // 验证数据
        if (!Array.isArray(historyData) || historyData.length === 0) {
            throw new Error('没有有效的历史数据可以显示');
        }

        // 隐藏加载状态
        document.getElementById('room-history-loading').style.display = 'none';
        document.getElementById('room-history-content').style.display = 'block';
        document.getElementById('room-history-error').style.display = 'none';

        // 获取表格元素和表格体
        const tableBody = document.getElementById('room-history-data');
        if (!tableBody) {
            console.error('找不到历史数据表格元素');
            return;
        }

        // 清空表格
        tableBody.innerHTML = '';

        // 准备数据 - 按时间顺序排序（从晚到早）
        const sortedData = [...historyData].sort((a, b) => new Date(b.query_time) - new Date(a.query_time));

        // 添加数据行
        sortedData.forEach(record => {
            const row = document.createElement('tr');

            // 格式化日期时间
            const date = new Date(record.query_time);
            const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;

            // 添加日期时间单元格
            const dateCell = document.createElement('td');
            dateCell.textContent = formattedDate;
            row.appendChild(dateCell);

            // 添加电量单元格
            const electricityCell = document.createElement('td');
            electricityCell.textContent = parseFloat(record.electricity).toFixed(2);
            row.appendChild(electricityCell);

            // 添加消耗电量单元格
            const consumptionCell = document.createElement('td');
            consumptionCell.textContent = record.consumption !== null ? record.consumption : '-';
            row.appendChild(consumptionCell);

            tableBody.appendChild(row);
        });

        // 创建电量图表
        createElectricityChart(historyData);
    } catch (error) {
        console.error('显示历史数据时出错:', error);
        document.getElementById('room-history-loading').style.display = 'none';
        document.getElementById('room-history-content').style.display = 'none';
        document.getElementById('room-history-error').style.display = 'block';
        document.getElementById('room-history-error').textContent = `显示历史数据失败: ${error.message}`;
    }
}

// 创建电量图表
function createElectricityChart(historyData) {
    try {
        // 获取画布元素
        const canvas = document.getElementById('electricityChart');
        if (!canvas) {
            console.error('无法找到图表画布元素');
            return;
        }

        const ctx = canvas.getContext('2d');

        // 准备数据 - 需要按时间顺序排序（从早到晚）
        const sortedData = [...historyData].sort((a, b) => new Date(a.query_time) - new Date(b.query_time));

        // 提取时间和电量数据
        const labels = sortedData.map(record => {
            const date = new Date(record.query_time);
            return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
        });
        const electricityValues = sortedData.map(record => parseFloat(record.electricity));

        // 提取消耗电量数据（如果有）
        const consumptionValues = sortedData.map(record => record.consumption ? parseFloat(record.consumption) : null);

        // 检查是否有消耗数据
        const hasConsumptionData = consumptionValues.some(value => value !== null);

        // 销毁可能存在的旧图表
        if (window.electricityChart && typeof window.electricityChart.destroy === 'function') {
            window.electricityChart.destroy();
            window.electricityChart = null;
        }

        // 准备数据集
        const datasets = [
            {
                label: '剩余电量(度)',
                data: electricityValues,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.2,
                fill: true,
                yAxisID: 'y'
            }
        ];

        // 如果有消耗数据，添加第二个数据集
        if (hasConsumptionData) {
            datasets.push({
                label: '消耗电量(度)',
                data: consumptionValues,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.2,
                fill: false,
                yAxisID: 'y1'
            });
        }

        // 创建图表配置
        const options = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || '';
                            const value = context.raw !== null ? context.raw.toFixed(2) + '度' : '无数据';
                            return `${label}: ${value}`;
                        }
                    }
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '剩余电量(度)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '查询时间'
                    }
                }
            }
        };

        // 如果有消耗数据，添加第二个Y轴
        if (hasConsumptionData) {
            options.scales.y1 = {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: '消耗电量(度)'
                },
                grid: {
                    drawOnChartArea: false,
                }
            };
        }

        // 检查Chart是否可用
        if (typeof Chart === 'undefined') {
            console.error('Chart.js库未加载');
            return;
        }

        // 创建图表
        window.electricityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: options
        });
    } catch (error) {
        console.error('创建电量图表时出错:', error);
    }
}

// 暴露一个测试函数，方便在控制台中测试
window.testHistoryAPI = function (timeId) {
    console.log(`直接测试API: /api/history_data/${timeId}`);

    // 创建一个新的事件，在页面中显示
    const testEvent = document.createElement('div');
    testEvent.className = 'alert alert-info';
    testEvent.style.position = 'fixed';
    testEvent.style.top = '10px';
    testEvent.style.right = '10px';
    testEvent.style.zIndex = '9999';
    testEvent.style.maxWidth = '400px';
    testEvent.innerHTML = `
        <strong>API测试:</strong> 
        <p>正在测试timeId: ${timeId}</p>
        <div class="progress mt-2">
            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                 style="width: 100%" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
    `;
    document.body.appendChild(testEvent);

    fetch(`/api/history_data/${timeId}`)
        .then(response => response.json())
        .then(data => {
            console.log('API返回数据:', data);

            // 更新测试事件显示
            testEvent.className = data.error ? 'alert alert-danger' : 'alert alert-success';
            testEvent.innerHTML = `
                <strong>API测试结果:</strong> 
                <p>timeId: ${timeId}</p>
                ${data.error ?
                    `<p class="text-danger">错误: ${data.error}</p>` :
                    `<p class="text-success">成功! 获取了 ${data.data ? data.data.length : 0} 条记录</p>`}
                <pre style="max-height: 200px; overflow: auto;">${JSON.stringify(data.debug_info || {}, null, 2)}</pre>
                <button class="btn btn-sm btn-secondary" id="close-test-event">关闭</button>
            `;

            // 添加关闭按钮事件
            document.getElementById('close-test-event').addEventListener('click', function () {
                document.body.removeChild(testEvent);
            });
        })
        .catch(error => {
            console.error('API测试出错:', error);

            // 更新测试事件显示
            testEvent.className = 'alert alert-danger';
            testEvent.innerHTML = `
                <strong>API测试错误:</strong> 
                <p>timeId: ${timeId}</p>
                <p class="text-danger">${error.message}</p>
                <button class="btn btn-sm btn-secondary" id="close-test-event">关闭</button>
            `;

            // 添加关闭按钮事件
            document.getElementById('close-test-event').addEventListener('click', function () {
                document.body.removeChild(testEvent);
            });
        });
}; 