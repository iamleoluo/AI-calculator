"""
Test V2 streaming API endpoint
"""
import requests
import json
import time

def test_streaming_endpoint():
    """Test the V2 streaming endpoint"""

    url = "http://localhost:8000/api/v2/fourier-series/stream"

    payload = {
        "function_expr": "np.sin(t)",
        "period": 6.283185,
        "n_terms": 3
    }

    print("=" * 80)
    print("Testing V2 Streaming API")
    print("=" * 80)
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    print("\nStreaming events:\n")

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return

        event_count = 0
        derivation_chunks = 0
        derivation_text = ""

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode('utf-8')

            # Parse SSE format
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix

                try:
                    event = json.loads(data)
                    event_count += 1

                    event_type = event.get('type', 'unknown')

                    # Display event info
                    if event_type == 'session_created':
                        print(f"✅ Session created: {event['session_id']}")

                    elif event_type == 'iteration_start':
                        print(f"\n🔄 Iteration {event['iteration']} started")

                    elif event_type == 'derivation_chunk':
                        derivation_chunks += 1
                        chunk = event.get('content', '')
                        derivation_text += chunk
                        # Show first few chunks
                        if derivation_chunks <= 5:
                            print(f"📝 Chunk {derivation_chunks}: {chunk[:50]}...")
                        elif derivation_chunks == 6:
                            print(f"📝 ... (streaming continues)")

                    elif event_type == 'derivation_complete':
                        print(f"\n✅ Derivation complete ({len(derivation_text)} chars)")

                    elif event_type == 'code_generated':
                        print(f"💻 Code generated")
                        # Show first few lines of code
                        code = event.get('code', {})
                        if 'original_function' in code:
                            lines = code['original_function'].split('\n')
                            print(f"   Original function: {lines[0][:60]}...")

                    elif event_type == 'verification_result':
                        result = event.get('result', {})
                        is_verified = result.get('is_verified', False)
                        error_metrics = result.get('error_metrics', {})
                        max_error = error_metrics.get('max_relative_error', 0)

                        if is_verified:
                            print(f"✅ Verification PASSED - Max error: {max_error*100:.6f}%")
                        else:
                            print(f"❌ Verification FAILED - Max error: {max_error*100:.6f}%")

                    elif event_type == 'error_analysis':
                        analysis = event.get('analysis', {})
                        category = analysis.get('error_category', 'unknown')
                        severity = analysis.get('severity', 'unknown')
                        need_retry = analysis.get('need_recalculation', False)
                        print(f"🧠 Error analysis: {category} ({severity}), Retry: {need_retry}")

                    elif event_type == 'success':
                        result = event.get('result', {})
                        print(f"\n🎉 SUCCESS!")
                        print(f"   Total iterations: {result.get('iterations', 1)}")

                        # Show verification details
                        verification = result.get('verification', {})
                        if verification:
                            error_metrics = verification.get('error_metrics', {})
                            print(f"   Max relative error: {error_metrics.get('max_relative_error', 0)*100:.6f}%")
                            print(f"   Mean relative error: {error_metrics.get('mean_relative_error', 0)*100:.6f}%")

                    elif event_type == 'success_with_warning':
                        result = event.get('result', {})
                        print(f"\n⚠️  SUCCESS WITH WARNING")
                        print(f"   Status: {result.get('status', 'unknown')}")
                        if 'error_analysis' in result:
                            analysis = result['error_analysis']
                            print(f"   Explanation: {analysis.get('explanation', 'N/A')}")

                    elif event_type == 'failed':
                        print(f"\n❌ FAILED: {event.get('reason', 'Unknown reason')}")

                    elif event_type == 'max_iterations_reached':
                        print(f"\n⚠️  Max iterations reached: {event.get('message', '')}")

                    else:
                        print(f"❓ Unknown event: {event_type}")

                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parse error: {e}")
                    print(f"   Data: {data[:100]}...")

        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print(f"Total events received: {event_count}")
        print(f"Derivation chunks: {derivation_chunks}")
        print(f"Total derivation length: {len(derivation_text)} characters")
        print(f"Elapsed time: {elapsed:.2f}s")
        print("=" * 80)

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")


if __name__ == "__main__":
    test_streaming_endpoint()
