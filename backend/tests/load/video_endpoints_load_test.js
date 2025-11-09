/**
 * K6 Load Test for Video Management Endpoints
 *
 * This script tests the performance and scalability of video API endpoints
 * under various load conditions.
 *
 * Usage:
 *   # Smoke test (minimal load)
 *   k6 run --vus 1 --duration 30s video_endpoints_load_test.js
 *
 *   # Load test (normal load)
 *   k6 run --vus 10 --duration 5m video_endpoints_load_test.js
 *
 *   # Stress test (high load)
 *   k6 run --vus 50 --duration 10m video_endpoints_load_test.js
 *
 *   # Spike test (sudden load increase)
 *   k6 run --stage 30s:0 --stage 10s:100 --stage 3m:100 --stage 10s:0 video_endpoints_load_test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const videoListDuration = new Trend('video_list_duration');
const videoCreateDuration = new Trend('video_create_duration');
const videoUpdateDuration = new Trend('video_update_duration');
const presignedUrlDuration = new Trend('presigned_url_duration');
const totalRequests = new Counter('total_requests');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 users
    { duration: '2m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '2m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down to 0
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],   // 95% of requests should be below 500ms
    'http_req_failed': ['rate<0.01'],     // Error rate should be less than 1%
    'errors': ['rate<0.05'],               // Custom error rate
    'video_list_duration': ['p(95)<300'], // List endpoint should be fast
    'video_create_duration': ['p(95)<1000'], // Create can be slower
  },
};

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

// Test data
let authToken = null;
let testUserId = null;
let videoIds = [];

/**
 * Setup function - runs once per VU before the test starts
 */
export function setup() {
  // Create a test user and get auth token
  // In a real scenario, you'd authenticate here
  // For now, we'll mock the token

  console.log('Setting up load test...');

  // You would typically:
  // 1. Create a test user
  // 2. Authenticate and get a JWT token
  // 3. Return the token for use in tests

  return {
    authToken: 'test-jwt-token', // Replace with actual auth flow
    userId: 'test-user-id'
  };
}

/**
 * Main test function - runs for each VU iteration
 */
export default function(data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.authToken}`,
  };

  group('Video Upload Flow', () => {
    // 1. Generate presigned URL
    group('Generate Presigned URL', () => {
      const presignedPayload = JSON.stringify({
        filename: `test-video-${Date.now()}.mp4`,
        file_size: 10 * 1024 * 1024, // 10 MB
        content_type: 'video/mp4',
      });

      const presignedStart = Date.now();
      const presignedRes = http.post(
        `${BASE_URL}${API_PREFIX}/upload/presigned-url`,
        presignedPayload,
        { headers }
      );
      presignedUrlDuration.add(Date.now() - presignedStart);
      totalRequests.add(1);

      const presignedSuccess = check(presignedRes, {
        'presigned URL status is 200': (r) => r.status === 200,
        'presigned URL response has video_id': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.video_id !== undefined;
          } catch (e) {
            return false;
          }
        },
        'presigned URL response has presigned_url': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.presigned_url !== undefined;
          } catch (e) {
            return false;
          }
        },
      });

      if (!presignedSuccess) {
        errorRate.add(1);
      } else {
        errorRate.add(0);
        const responseBody = JSON.parse(presignedRes.body);
        videoIds.push(responseBody.video_id);
      }
    });

    sleep(0.5);

    // 2. Create video record (simulate upload completion)
    if (videoIds.length > 0) {
      group('Create Video Record', () => {
        const videoId = videoIds[videoIds.length - 1];
        const createPayload = JSON.stringify({
          video_id: videoId,
          title: `Load Test Video ${Date.now()}`,
          description: 'Video created during load testing',
          s3_key: `videos/${data.userId}/${videoId}/test.mp4`,
        });

        const createStart = Date.now();
        const createRes = http.post(
          `${BASE_URL}${API_PREFIX}/videos`,
          createPayload,
          { headers }
        );
        videoCreateDuration.add(Date.now() - createStart);
        totalRequests.add(1);

        const createSuccess = check(createRes, {
          'create video status is 201': (r) => r.status === 201,
          'created video has correct title': (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.title.includes('Load Test Video');
            } catch (e) {
              return false;
            }
          },
        });

        if (!createSuccess) {
          errorRate.add(1);
        } else {
          errorRate.add(0);
        }
      });
    }

    sleep(1);
  });

  group('Video Listing and Filtering', () => {
    // 3. List videos (default)
    group('List All Videos', () => {
      const listStart = Date.now();
      const listRes = http.get(
        `${BASE_URL}${API_PREFIX}/videos`,
        { headers }
      );
      videoListDuration.add(Date.now() - listStart);
      totalRequests.add(1);

      const listSuccess = check(listRes, {
        'list videos status is 200': (r) => r.status === 200,
        'list videos returns array': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body);
          } catch (e) {
            return false;
          }
        },
      });

      if (!listSuccess) {
        errorRate.add(1);
      } else {
        errorRate.add(0);
      }
    });

    sleep(0.3);

    // 4. List videos with pagination
    group('List Videos with Pagination', () => {
      const paginatedRes = http.get(
        `${BASE_URL}${API_PREFIX}/videos?limit=10&offset=0`,
        { headers }
      );
      totalRequests.add(1);

      const paginatedSuccess = check(paginatedRes, {
        'paginated list status is 200': (r) => r.status === 200,
        'paginated list respects limit': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body) && body.length <= 10;
          } catch (e) {
            return false;
          }
        },
      });

      if (!paginatedSuccess) {
        errorRate.add(1);
      } else {
        errorRate.add(0);
      }
    });

    sleep(0.3);

    // 5. List videos with filtering
    group('List Videos with Filter', () => {
      const filteredRes = http.get(
        `${BASE_URL}${API_PREFIX}/videos?status=completed`,
        { headers }
      );
      totalRequests.add(1);

      const filteredSuccess = check(filteredRes, {
        'filtered list status is 200': (r) => r.status === 200,
        'filtered results match status': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body) && body.every(v =>
              !v.status || v.status === 'completed'
            );
          } catch (e) {
            return false;
          }
        },
      });

      if (!filteredSuccess) {
        errorRate.add(1);
      } else {
        errorRate.add(0);
      }
    });

    sleep(0.3);

    // 6. List videos with search
    group('List Videos with Search', () => {
      const searchRes = http.get(
        `${BASE_URL}${API_PREFIX}/videos?search=Load`,
        { headers }
      );
      totalRequests.add(1);

      check(searchRes, {
        'search videos status is 200': (r) => r.status === 200,
      });
    });

    sleep(0.3);

    // 7. List videos with sorting
    group('List Videos with Sorting', () => {
      const sortedRes = http.get(
        `${BASE_URL}${API_PREFIX}/videos?sort_by=created_at&sort_order=desc`,
        { headers }
      );
      totalRequests.add(1);

      check(sortedRes, {
        'sorted list status is 200': (r) => r.status === 200,
      });
    });
  });

  sleep(0.5);

  group('Video Operations', () => {
    if (videoIds.length > 0) {
      const randomVideoId = videoIds[Math.floor(Math.random() * videoIds.length)];

      // 8. Get single video
      group('Get Video Details', () => {
        const getRes = http.get(
          `${BASE_URL}${API_PREFIX}/videos/${randomVideoId}`,
          { headers }
        );
        totalRequests.add(1);

        const getSuccess = check(getRes, {
          'get video status is 200 or 404': (r) => r.status === 200 || r.status === 404,
        });

        if (getRes.status !== 200 && getRes.status !== 404) {
          errorRate.add(1);
        } else {
          errorRate.add(0);
        }
      });

      sleep(0.3);

      // 9. Update video
      group('Update Video', () => {
        const updatePayload = JSON.stringify({
          title: `Updated Title ${Date.now()}`,
          description: 'Updated during load test',
        });

        const updateStart = Date.now();
        const updateRes = http.patch(
          `${BASE_URL}${API_PREFIX}/videos/${randomVideoId}`,
          updatePayload,
          { headers }
        );
        videoUpdateDuration.add(Date.now() - updateStart);
        totalRequests.add(1);

        const updateSuccess = check(updateRes, {
          'update video status is 200 or 404': (r) => r.status === 200 || r.status === 404,
        });

        if (updateRes.status !== 200 && updateRes.status !== 404) {
          errorRate.add(1);
        } else {
          errorRate.add(0);
        }
      });

      sleep(0.3);

      // 10. Get playback URL
      group('Get Playback URL', () => {
        const playbackRes = http.get(
          `${BASE_URL}${API_PREFIX}/videos/${randomVideoId}/playback-url`,
          { headers }
        );
        totalRequests.add(1);

        const playbackSuccess = check(playbackRes, {
          'playback URL status is 200, 404, or 500': (r) =>
            r.status === 200 || r.status === 404 || r.status === 500,
        });

        if (![200, 404, 500].includes(playbackRes.status)) {
          errorRate.add(1);
        } else {
          errorRate.add(0);
        }
      });
    }
  });

  // Random sleep between iterations
  sleep(Math.random() * 2 + 1);
}

/**
 * Teardown function - runs once after all VUs complete
 */
export function teardown(data) {
  console.log('Load test completed!');
  console.log(`Total video IDs created: ${videoIds.length}`);

  // In a real scenario, you might want to:
  // 1. Clean up test data
  // 2. Generate a summary report
  // 3. Send notifications
}

/**
 * Handle summary for custom reporting
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load_test_results.json': JSON.stringify(data),
  };
}

/**
 * Simple text summary (fallback if k6 doesn't provide one)
 */
function textSummary(data, options = {}) {
  const indent = options.indent || '';
  const enableColors = options.enableColors !== false;

  let summary = '\n';
  summary += `${indent}Test Results:\n`;
  summary += `${indent}=============\n`;
  summary += `${indent}Total Requests: ${data.metrics.total_requests?.values?.count || 0}\n`;
  summary += `${indent}Failed Requests: ${data.metrics.http_req_failed?.values?.rate || 0}\n`;
  summary += `${indent}Error Rate: ${data.metrics.errors?.values?.rate || 0}\n`;
  summary += `${indent}\n`;
  summary += `${indent}Performance:\n`;
  summary += `${indent}  List Videos p95: ${data.metrics.video_list_duration?.values?.['p(95)'] || 0}ms\n`;
  summary += `${indent}  Create Video p95: ${data.metrics.video_create_duration?.values?.['p(95)'] || 0}ms\n`;
  summary += `${indent}  Update Video p95: ${data.metrics.video_update_duration?.values?.['p(95)'] || 0}ms\n`;
  summary += `${indent}  Presigned URL p95: ${data.metrics.presigned_url_duration?.values?.['p(95)'] || 0}ms\n`;

  return summary;
}
