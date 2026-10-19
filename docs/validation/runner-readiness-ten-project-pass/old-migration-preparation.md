# Old-project native migration preparation

`old-migration-native-preparation.json` inventories 274 prepared contracts
across the original 21 native profiles of ten historical applications. Every
package preserves its original native command, input/screen/exit prefix,
fixture bytes and snapshot bytes. Public v3 saved-state steps append after
completion. Native suffix selection follows the original public-command
driver, including the reviewed Windows and Unix cancellation variants.

The first complete preparation attempt stopped at Broot's deliberately removed
generated large fixture. Its partial package and file-hash index remain under
the owned migration directory. The corrected preparation regenerated only
that fixture into the new package through the original reviewed generator,
checking its entire file mapping against the original scenario. It did not
recreate or modify the historical campaign's fixture directory. Explicit
fixture-directory declarations are restored into new packages where present.

This is preparation only: no historical application has been reacquired or
executed for migration. Migrated projects, native migration executions and
new-project credit remain zero. Each application still needs scoped setup,
all applicable ordinary tests, real corruption/recovery controls, independent
audit and cleanup before any migration claim.
