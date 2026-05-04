<!-- lang-dotnet.md -->
## dotnet / csharp

### Target framework and language version

- Respect the `<TargetFramework>` in `.csproj`. Do not change it without explicit instruction.
- Match the C# language version (`<LangVersion>`) already set in the project. Do not opt into newer features that change semantics.
- If the project enables nullable reference types (`<Nullable>enable</Nullable>`), treat all nullable warnings as errors — do not suppress them with `!` unless genuinely correct.

### Async

- `async` all the way down. Do not block on async code with `.Result`, `.Wait()`, or `GetAwaiter().GetResult()` — this causes deadlocks in ASP.NET contexts.
- Use `ConfigureAwait(false)` in library code (class libraries, NuGet packages). In application code (ASP.NET controllers, Blazor components) it is not required.
- `CancellationToken` should flow through any method that does I/O. Accept it as a parameter; do not create `new CancellationTokenSource()` internally unless managing a timeout.
- Never use `async void` except for event handlers. All other async methods return `Task` or `Task<T>`.

### Error handling

- Catch specific exception types. Do not catch `Exception` at a low level unless re-throwing or logging-and-rethrowing.
- Do not swallow exceptions silently. At minimum, log before swallowing.
- Use `when` clauses in `catch` to filter without unwinding the stack unnecessarily.
- Validate arguments at public API boundaries and throw `ArgumentNullException`, `ArgumentOutOfRangeException`, etc. with the parameter name.

### Dependency injection

- Follow the existing DI registration pattern in `Program.cs` / `Startup.cs`. Do not introduce a second container.
- Register services with the narrowest appropriate lifetime: `Scoped` for request-scoped, `Singleton` for stateless, `Transient` sparingly.
- Do not resolve services from the container manually (service locator pattern) unless the repo already does so.

### Code style

- Use `var` when the type is obvious from the right-hand side. Use the explicit type when it aids clarity.
- Prefer LINQ for readability. Avoid LINQ chains longer than ~4 clauses — break into named intermediates or a loop.
- Use expression-bodied members only when the body is genuinely a single expression, not to compress multi-step logic.
- Do not use `#region` unless the file already uses it.
- Remove all `Console.WriteLine` and `Debug.WriteLine` debug statements before committing.

### Security

- Do not interpolate user input into SQL strings. Use parameterized queries or an ORM.
- Do not interpolate user input into file paths without sanitization and path canonicalization checks.
- Do not store secrets in `appsettings.json` committed to source control. Use environment variables, `dotnet user-secrets`, or a secrets manager.
- Hash passwords with `BCrypt`, `Argon2`, or ASP.NET Core's `IPasswordHasher<T>` — never `MD5` or `SHA1` alone.

### Testing

- Match the existing test framework (xUnit, NUnit, MSTest). Do not introduce a second one.
- Use `FluentAssertions` or `Shouldly` if the repo already has them; otherwise use the framework's built-in assertions.
- Each test must be independent — no shared mutable state across tests.
- Mock dependencies at the interface boundary using the repo's existing mock library (Moq, NSubstitute, etc.).

### Validation

```bash
dotnet build                # must succeed with 0 errors, 0 warnings (or match repo baseline)
dotnet test                 # full test suite
dotnet format --verify-no-changes  # formatting check (if dotnet-format is configured)
```

Do not claim tests pass unless `dotnet test` was actually run and exited 0.
