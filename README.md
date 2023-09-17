# pet-demo

```
bazel build //proto:pet_common_proto

bazel build //proto:pet_service_proto
```

```
bazel build //proto/pet:pet_python_grpc

bazel build //service:service_bin

bazel-bin/service/service_bin
```
