# kubectl Debugging & Monitoring Cheat Sheet

Reference commands for debugging and monitoring pods in the `GetMeTo-API` cluster (and generally, any k8s cluster).

## Glossary — Placeholder Parameters

| Placeholder | Stands for | Example value (this cluster) |
|---|---|---|
| `<ns>` | Namespace | `dev` |
| `<pod>` | Pod name | `getmeto-api-598dbbdf84-ghb65` |
| `<name>` | Deployment name | `getmeto-api` |
| `<file>` | Path to a manifest file | `k8s-base.yaml`, `k8s-deployment.yaml` |
| `<label>` | A label selector key=value pair | `app.kubernetes.io/name=getmeto-api` |
| `<node>` | Node name | `i-0426c4578c5110cc2` |
| `<n>` | A revision number (integer) | `3` (as in `--to-revision=3`) |

**Notes:**
- `-n` is short for `--namespace` (`-n dev` == `--namespace dev`). Omitting `-n` uses your context's default namespace, not "all namespaces." Use `-A` / `--all-namespaces` to search everywhere.
- `-o` is short for `--output` (e.g. `-o yaml`, `-o wide`, `-o jsonpath='...'`) — controls output format, not what's fetched.

---

## Must Know

| Name | Command | Description | When to Use | Comment |
|---|---|---|---|---|
| Get pods | `kubectl get pods -n <ns>` | Lists pods with status, restarts, age | First command, always — quick health snapshot | Add `-o wide` to see node/IP; add `-w` to watch live |
| Describe pod | `kubectl describe pod <pod> -n <ns>` | Full pod spec, status, conditions, and Events log | When a pod isn't Ready/Running and you need to know *why* | The `Events` section at the bottom is almost always where the real answer is |
| Pod logs | `kubectl logs <pod> -n <ns>` | Prints container stdout/stderr | App crashed or is misbehaving and you need its output | If the container already restarted, current logs may be empty — see `--previous` below |
| Previous container logs | `kubectl logs <pod> -n <ns> --previous` | Logs from the *last* terminated instance of the container | `CrashLoopBackOff` — current logs show nothing useful because it just restarted | This is exactly what caught the Pydantic `ValidationError` traceback |
| Get deployment | `kubectl get deployment <name> -n <ns>` | Shows desired vs. current vs. available replicas | Quick check: is my rollout actually healthy? | `READY 2/2` is what you want; `1/2` means something's stuck |
| Describe deployment | `kubectl describe deployment <name> -n <ns>` | Full rollout state: conditions, old/new ReplicaSets, events | Rollout stuck or timed out | `Conditions: Progressing = False, Reason: ProgressDeadlineExceeded` is the classic stuck-rollout signature |
| Get events (cluster-wide) | `kubectl get events -n <ns> --sort-by='.lastTimestamp'` | All recent events in the namespace, chronological | Something's wrong but you don't even know which pod yet | Faster than describing every pod one by one when triaging |
| Exec into pod | `kubectl exec -it <pod> -n <ns> -- /bin/sh` | Opens a shell inside the running container | App is up but behaving wrong — need to poke around, check files/env | Won't work if the container keeps crashing before you can attach |
| Rollout status | `kubectl rollout status deployment/<name> -n <ns>` | Blocks and reports whether a rollout succeeded or is stuck | Right after a deploy, or in CI, to gate success/failure | This is the command your pipeline uses — same one you can run manually |
| Get all in namespace | `kubectl get all -n <ns>` | Lists pods, deployments, services, replicasets at once | Quick full-namespace overview | Doesn't include ConfigMaps/Secrets — those need a separate `get` |

---

## Very Useful

| Name | Command | Description | When to Use | Comment |
|---|---|---|---|---|
| Get pods by label | `kubectl get pods -n <ns> -l <label>` | Filters pods by label selector | Multiple apps/ReplicaSets in one namespace and you only care about one | This is exactly how you isolate `getmeto-api`'s pods from everything else in `dev` |
| Top pods (resource usage) | `kubectl top pods -n <ns>` | Live CPU/memory usage per pod | Suspected resource pressure, OOMKills, or picking `requests`/`limits` values | Requires `metrics-server` installed on the cluster |
| Get pod YAML (live state) | `kubectl get pod <pod> -n <ns> -o yaml` | Full live object as YAML, including status | Need to see exact current state vs. what you *think* you applied | This is how you confirm a ConfigMap's `resourceVersion` hasn't changed |
| Diff before apply | `kubectl diff -f <file>` | Shows what would change *before* you apply it | Before any manual `kubectl apply`, especially on shared/prod namespaces | Would have caught the image-tag regression before it happened |
| Port-forward | `kubectl port-forward pod/<pod> 8000:8000 -n <ns>` | Tunnels a local port to a port inside the pod | Testing `/health` or an endpoint directly, bypassing the Service/Ingress | Great for isolating "is it the app or is it the Service/routing" |
| Get replicasets | `kubectl get replicasets -n <ns> -l <label>` | Lists ReplicaSets, including old/stale ones | After a rollout, to check for leftover ReplicaSets from failed deploys | Exactly what surfaces stale ReplicaSets stuck on old image tags |
| Rollout history | `kubectl rollout history deployment/<name> -n <ns>` | Lists past revisions of a Deployment | Need to know what changed across revisions, or want to roll back | Pair with `kubectl rollout undo` to revert to a previous revision |
| Rollout undo | `kubectl rollout undo deployment/<name> -n <ns>` | Reverts to the previous (or a specific) revision | A bad deploy just went out and you need to revert fast | `--to-revision=<n>` targets a specific historical revision |
| Get pod's node | `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.nodeName}'` | Prints just the node a pod is scheduled on | Suspect a node-level issue (disk pressure, network) affecting multiple pods | Pairs well with `kubectl describe node <node>` |
| Check configmap/secret refs | `kubectl get pod <pod> -n <ns> -o yaml \| grep -A5 envFrom` | Shows what ConfigMaps/Secrets a running pod is actually wired to | Confirming a pod is reading the config you *think* it's reading | Cheap sanity check before chasing a harder bug |
| Delete stuck pod | `kubectl delete pod <pod> -n <ns>` | Force-deletes a pod; Deployment recreates it | Pod stuck in a bad state and you want a clean restart | Safe under a Deployment/ReplicaSet — it'll just spin up a fresh replacement |
| Watch resource live | `kubectl get pods -n <ns> -w` | Streams live updates as pod state changes | Watching a rollout or restart happen in real time | `-w` works on most `get` commands, not just pods |